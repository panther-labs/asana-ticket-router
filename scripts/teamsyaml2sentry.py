import yaml

TEAMS_YAML_LOCATION='../sentry_asana/src/common/components/entities/data/teams.yaml'

with open(TEAMS_YAML_LOCATION, "r") as stream:
    teams_data = yaml.safe_load(stream)
    sentry_config = ""
    for team in teams_data:
        team_name = team['name']
        team_name = team_name.lower().replace(' ', '-')

        for entity in team['Entities']:
            for match in entity['Matchers']:

                #Unescape our periods. Sentry wants unix style globs not regex.
                # https://docs.sentry.io/product/issues/issue-owners/
                match = match.replace('\\.', '.')

                if 'server_name:' in match:
                    #Turn single slash regex into unix style globs
                    #Ex:  Matchers: ["server_name:/\\.compute\\.internal/"] -> tags.server_name:*.ec2.internal*

                    match = match.replace('/', '*')
                    sentry_config += f'tags.{match} #{team_name}\n'
                if 'url:' in match:
                    #Turn escaped double slash regex into unix style globs
                    #Ex: Matchers: ["url://alerts-and-errors//"] -> url:*/alerts-and-errors/*

                    #beginning match.
                    match = match.replace('//','*/', 1)

                    #end match
                    match = match.replace('//','/*', 1)

                    sentry_config += f'{match} #{team_name}\n'

    print(sentry_config)
