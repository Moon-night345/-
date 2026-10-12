from ..navigation import navigation_for
def run(level,lang='en'): return {'agent':'navigation',**navigation_for(level,lang)}
