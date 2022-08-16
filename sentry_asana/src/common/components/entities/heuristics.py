"""Heuristics maps a 'resource' to 'team'"""

from typing import Optional, Tuple, List
from common.components.entities import service


class TeamNotFound(Exception):
    """Error handling for Team not found team routing."""


def get_team(
    teams_service: service.TeamService, resource: dict
) -> Tuple[service.EngTeam, List[service.MatchResult]]:
    """GetTeam returns the engTeam for a given resource, or a TeamNotFound exception if no team could be matched.
    If callers get a TeamNotFound, the best solution is to call teams_sevice.default_team() and use that.

    """
    team = precedence_match_team(teams_service, resource)
    if team[0] is None:
        raise TeamNotFound
    return team


def precedence_match_team(
    teams_service: service.TeamService, resource: dict
) -> Tuple[Optional[service.EngTeam], List[service.MatchResult]]:
    """PrecedenceMatchTeam implements tag-precedence as loosely described in the tech spec.
    https://www.notion.so/pantherlabs/Datadog2Asana-7a206f017b1b4befaedba417b2dd5e3e

    Consider some examples:

    Team1: { Entities: [EntityMatcher: {Tags: ['service:foo']}]}
    Team2: { Entities: [EntityMatcher: {Tags: ['team:bar']}]}
    entity={'service':'foo', 'team':'bar'}

    Both teams will match the entity with the same number of matchers (1), but team has a higher precedence, so the team matcher 'wins'.

    Imagine a case where we have lots of tags (so specific!) but not the team tag!

    Team1: {Entities: [EntityMatcher: {Tags: ['specific1:12345', 'specific2:39742', 'specific3:134974']}]}
    Team2: {Entities: [EntityMatcher: {Tags: ['team:bar','specific1:12345']}]}
    entity={'team': 'bar', 'specific1':'12345', 'specific2':'39742', 'specific3':'134974}

    Without precedence, the first tag matcher would win (It has more matches, 3 vs 2), but we want the second matcher to
    rank higher because team matches are 'better' (have higher precedence.)
    """
    ranks = []
    # Try to match this resource against all known entity matchers.
    for team in teams_service.get_teams():
        for matcher in team.Entities:
            matches = matcher.match_rank(resource)
            if matches is not None:
                ranks.append((team, matches))
    # sort by precedence, then by rank.
    ranks = sorted(
        ranks, key=lambda x: (x[1].Precedence, len(x[1].Matches)), reverse=True
    )
    if ranks:
        # return top match
        return ranks[0]
    return (None, [])
