import os
import json
import click
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


def get_env_var_str(env_vars):
    env_var_list = []
    [env_var_list.append('{key: "' + env_var['key'] + '", value: """' + env_var['value'] + '""", isSecret: ' + str(env_var['isSecret']).lower() + '}') for env_var in env_vars]
    env_vars_str = ', '.join(env_var_list)
    
    return env_vars_str
    
    
def set_env_var_query(endpoint, deployment_id, release_name, env_vars, upsert_batch_size):
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
        '''.replace("$deploymentId", deployment_id).replace("$releaseName", release_name)
    
    env_vars_ct = len(env_vars)
    for i in range(0, env_vars_ct, upsert_batch_size):        
        env_var_str = get_env_var_str(env_vars[i:min(env_vars_ct, i+upsert_batch_size)])
        env_vars_response = endpoint(query.replace("$envVars", env_var_str))


@click.command()
@click.option('--env_var_json_file', default=None, help='optional json formatted environment variables file')
#@click.option('--upsert_batch_size', default=10 help='specify upsert batch size, default 10')
def main(env_var_json_file): 
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
        
        if env_var_json_file:
            print("loading env vars from json file")
            env_vars = json.load(open(env_var_json_file))
            
        else:
            print("getting env vars from graphql")
            get_env_vars_response = endpoint(get_env_var_query(source_workspace_id, source_release_name))
            env_vars = get_env_vars_response['data']['workspaceDeployments'][0]['environmentVariables']
        
        [print(env_var) for env_var in env_vars]

        get_deployment_id_response = endpoint(get_deployment_id_query(dest_workspace_id, dest_release_name))
        deployment_id = get_deployment_id_response['data']['workspaceDeployments'][0]['id']
        print(deployment_id)

        # running mutation overwrites all existing env vars
        # although call to endpoint returns immediately, actual deployment of update will take several seconds - check UI
        upsert_batch_size=len(env_vars)
        set_env_var_query(endpoint, deployment_id, dest_release_name, env_vars, upsert_batch_size)

    except Exception as e:
        print(f"exception occurred: {e}")


if __name__ == '__main__':
    print('in main()')
    main()
