"""
Thompson Family Context
Rich family information for personalized memory assistance
"""

FAMILY_CONTEXT = """
PATIENT: John Thompson (Age 72)
- The family's unofficial peacekeeper
- Harry's go-to victim for new gadget trials
- Rae's favorite person to gossip with

SIBLINGS:

Harry Thompson (Age 66)
- John's younger brother
- Semi-retired electrical technician / part-time "garage inventor"
- Location: Brookhill, the quiet coastal town
- Personality: Builds strange devices, home-brews beer, fixes things no one asked him to fix
- Fun Facts:
  * Gives names to his tools ("Larry the Ladder" and "Sandy the Sander")
  * Has a running rivalry with neighborhood squirrels
  * Once built a solar-powered toaster that only works on cloudy days
  * Made a homemade drone that delivered one sandwich straight into a tree

Rae Thompson (Age 62)
- John's younger sister
- Interior design consultant / "social energy enhancer"
- Personality: Loves redecorating, astrology, scented candles, themed brunches
- Fun Facts:
  * Has three chihuahuas named after 90s pop stars
  * Sends inspirational quotes at 6 a.m.
  * Tried to start a gossip podcast (made 3 episodes, all about Harry)
  * Calls every minor inconvenience "a chapter in her redemption arc"

PARENTS:

Walter Thompson (Age 84)
- Retired navy mechanic
- Voice that could quiet an entire room
- Morning ritual: polishing old tools while whistling off-key
- Drives a 1989 truck that rattles like a drum kit
- Claims he has "a secret recording session with Elvis"

Elaine Thompson (Age 81)
- Retired school librarian
- Remembers every book anyone has ever borrowed
- Tends herb garden and bakes desserts "from scratch"
- Guards her recipes like classified state secrets
- Calls her grown children "my babies"
- Her apple pie mysteriously appears when family tensions rise

FAMILY VIBE:
The Thompsons don't do quiet. Between Harry's experiments, Rae's matchmaking chaos, and John's peacekeeping attempts, their home is a living sitcom. Every argument is funny in hindsight, every meal comes with a story.
"""

RELATIONSHIP_MAP = {
    'harry': {
        'relation': 'your younger brother',
        'age': 66,
        'personality': 'the inventor who builds strange gadgets',
        'fun_fact': 'He once built a drone that delivered a sandwich into a tree!'
    },
    'rae': {
        'relation': 'your younger sister',
        'age': 62,
        'personality': 'the social butterfly who loves decorating and gossip',
        'fun_fact': 'She has three chihuahuas named after 90s pop stars!'
    },
    'walter': {
        'relation': 'your father',
        'age': 84,
        'personality': 'the retired navy mechanic with the booming voice',
        'fun_fact': 'He still drives his 1989 truck that rattles like a drum kit!'
    },
    'elaine': {
        'relation': 'your mother',
        'age': 81,
        'personality': 'the retired librarian who bakes amazing desserts',
        'fun_fact': 'Her apple pie magically appears when the family argues!'
    }
}

def get_person_context(person_name: str) -> dict:
    """Get rich context about a family member"""
    return RELATIONSHIP_MAP.get(person_name.lower(), {
        'relation': person_name,
        'personality': 'a family member',
        'fun_fact': ''
    })
