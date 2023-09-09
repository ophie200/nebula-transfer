import os
from sgqlc.endpoint.requests import RequestsEndpoint


def get_env_var_query(workspace_id, release_name):
    query = '''
            query workspaceDeployments {
                workspaceDeployments(
                    workspaceUuid: "$workspaceId"
                    releaseName: "$releaseName"
                )
                {
                    environmentVariables { key, value, isSecret }
                }
            }
        '''.replace("$workspaceId", workspace_id).replace("$releaseName", release_name)
    print(query)
        
    return query


def get_deployment_id_query(workspace_id, release_name):
    query = '''
            query workspaceDeployments {
                workspaceDeployments(
                    workspaceUuid: "$workspaceId"
                    releaseName: "$releaseName"
                )
                {
                    id
                }
            }
        '''.replace("$workspaceId", workspace_id).replace("$releaseName", release_name)
    print(query)

    return query


def set_env_var_query(deployment_id, release_name, env_vars):
    env_var_list = []
    [env_var_list.append('{key: "' + env_var['key'] + '", value: "' + env_var['value'] + '", isSecret: ' + str(env_var['isSecret']).lower() + '}') for env_var in env_vars]
    env_vars_str = ', '.join(env_var_list)
    
    print(env_vars_str)
        
    query = '''
            mutation UpdateDeploymentVariables {
                updateDeploymentVariables(
                    deploymentUuid: "$deploymentId",
                    releaseName: "$releaseName",
                    environmentVariables: [
                        $envVars
                    ]
                ) {
                    key
                    value
                    isSecret
                }
            }
        '''.replace("$deploymentId", deployment_id).replace("$releaseName", release_name).replace("$envVars", env_vars_str)
    # print(query)
        
    return query


def main():
    try: 
        token = os.environ["NEBULA_DEPLOYMENT_TOKEN"]
        
        source_workspace_id = os.environ["SOURCE_WORKSPACE_ID"]
        source_release_name = os.environ["SOURCE_RELEASE_NAME"]

        dest_workspace_id = os.environ["DEST_WORKSPACE_ID"]
        dest_release_name = os.environ["DEST_RELEASE_NAME"]

        # create graphQL endpoint
        url = "https://houston.gcp0001.us-east4.astronomer.io/v1/"
        headers = {"authorization": token}
        endpoint = RequestsEndpoint(url, headers)
        
        # run query
        get_env_vars_response = endpoint(get_env_var_query(source_workspace_id, source_release_name))
        env_vars = get_env_vars_response['data']['workspaceDeployments'][0]['environmentVariables']
        # [print(env_var) for env_var in env_vars]

        get_deployment_id_response = endpoint(get_deployment_id_query(dest_workspace_id, dest_release_name))
        deployment_id = get_deployment_id_response['data']['workspaceDeployments'][0]['id']

        # will overwrite existing matching keys with
        # although call to endpoint returns, actual deployment of update will take several seconds - check UI
        env_vars_response = endpoint(set_env_var_query(deployment_id, dest_release_name, env_vars))
        print(env_vars_response)

    except Exception as e:
        print(f"exception occurred: {e}")


if __name__ == '__main__':
    print('in main()')
    main()
