"""Ship a public starter deck.

A brand new install has no word lists, so the first visitor sees an empty
Explore page and a game with nothing to play. This deck gives everyone
something to swipe on the first visit, with no account and no upload.

The words are stored here rather than in a fixture so that a fresh deploy is
playable straight after `migrate`, with no extra command to remember.
"""

from django.db import migrations

STARTER_LIST_NAME = 'Everyday English'
STARTER_SHARE_CODE = 'START1'

# word, definition, example
STARTER_WORDS = [
    ('abundant', 'Present in large quantity; more than enough.', 'The region has abundant rainfall.'),
    ('adamant', 'Refusing to change your mind.', 'She was adamant that she had locked the door.'),
    ('adequate', 'Good enough for what is needed.', 'The room had adequate light for reading.'),
    ('ambiguous', 'Open to more than one meaning; unclear.', 'His answer was deliberately ambiguous.'),
    ('arbitrary', 'Chosen by personal whim rather than by reason.', 'The deadline felt arbitrary.'),
    ('articulate', 'Able to express ideas clearly.', 'She is an articulate speaker.'),
    ('candid', 'Honest and direct, even when awkward.', 'He gave a candid account of the failure.'),
    ('coherent', 'Logical and consistent; easy to follow.', 'The report offered a coherent argument.'),
    ('compelling', 'So convincing or interesting that it holds attention.', 'A compelling reason to stay.'),
    ('concise', 'Saying much in few words.', 'Keep the summary concise.'),
    ('conventional', 'Following what is usually done.', 'They chose a conventional design.'),
    ('credible', 'Able to be believed.', 'The witness seemed credible.'),
    ('deliberate', 'Done on purpose, after thought.', 'It was a deliberate decision, not an accident.'),
    ('diligent', 'Careful and hard working.', 'A diligent student checks every answer.'),
    ('diminish', 'To become or make smaller or weaker.', 'The noise diminished as we walked away.'),
    ('discreet', 'Careful not to attract attention or reveal private things.', 'He made a discreet enquiry.'),
    ('elaborate', 'Detailed and complicated; or to explain in more detail.', 'Could you elaborate on that point?'),
    ('eloquent', 'Speaking or writing in a fluent, persuasive way.', 'An eloquent defence of the plan.'),
    ('ephemeral', 'Lasting a very short time.', 'Fame can be ephemeral.'),
    ('evident', 'Plain to see or understand.', 'Her relief was evident.'),
    ('exacerbate', 'To make a bad situation worse.', 'Shouting only exacerbated the argument.'),
    ('explicit', 'Stated clearly and in detail, leaving no doubt.', 'She gave explicit instructions.'),
    ('feasible', 'Possible to do easily or conveniently.', 'Finishing today is not feasible.'),
    ('fluctuate', 'To rise and fall irregularly.', 'Prices fluctuate through the year.'),
    ('fundamental', 'Forming a necessary base; essential.', 'Trust is fundamental to the team.'),
    ('futile', 'Pointless, because it has no chance of success.', 'Further argument was futile.'),
    ('hinder', 'To make something difficult or slow.', 'Heavy rain hindered the search.'),
    ('hypothesis', 'An idea put forward as a starting point for testing.', 'The data supported her hypothesis.'),
    ('imminent', 'About to happen very soon.', 'A storm was imminent.'),
    ('impartial', 'Not favouring one side over another.', 'An impartial referee.'),
    ('implicit', 'Suggested without being said directly.', 'There was an implicit warning in his tone.'),
    ('inevitable', 'Certain to happen; unavoidable.', 'Change was inevitable.'),
    ('ingenious', 'Clever, original and inventive.', 'An ingenious solution to an old problem.'),
    ('inherent', 'Existing as a natural, permanent part of something.', 'Risk is inherent in the sport.'),
    ('intricate', 'Very detailed and complicated.', 'An intricate pattern of lines.'),
    ('lucid', 'Clear and easy to understand.', 'A lucid explanation of the theory.'),
    ('meticulous', 'Showing great attention to detail.', 'He keeps meticulous records.'),
    ('mitigate', 'To make something less severe.', 'Shade mitigates the heat.'),
    ('negligible', 'So small that it is not worth considering.', 'The cost difference was negligible.'),
    ('novel', 'New and different from what came before.', 'A novel approach to the problem.'),
    ('nuance', 'A very small difference in meaning or feeling.', 'She caught every nuance of his tone.'),
    ('obsolete', 'No longer in use; out of date.', 'The format is now obsolete.'),
    ('plausible', 'Seeming reasonable or probably true.', 'That is a plausible explanation.'),
    ('pragmatic', 'Dealing with things practically rather than ideally.', 'A pragmatic choice under pressure.'),
    ('precedent', 'An earlier case used as a guide for later ones.', 'The ruling set a precedent.'),
    ('profound', 'Very great, or showing deep understanding.', 'The book had a profound effect on her.'),
    ('prohibit', 'To formally forbid.', 'The rules prohibit late entries.'),
    ('prominent', 'Important, or easily seen.', 'A prominent scientist spoke first.'),
    ('redundant', 'No longer needed; repeated unnecessarily.', 'Cut the redundant sentences.'),
    ('reluctant', 'Unwilling, and therefore slow to act.', 'He was reluctant to admit the mistake.'),
    ('resilient', 'Able to recover quickly from difficulty.', 'Children are remarkably resilient.'),
    ('rigorous', 'Extremely thorough and careful.', 'The study used rigorous methods.'),
    ('scrutiny', 'Close and careful examination.', 'The accounts came under scrutiny.'),
    ('subsequent', 'Coming after something else in time.', 'Subsequent tests confirmed the result.'),
    ('substantial', 'Large in size, value or importance.', 'A substantial improvement.'),
    ('sufficient', 'As much as is needed.', 'We have sufficient time.'),
    ('tangible', 'Real enough to be touched or clearly seen.', 'Tangible progress at last.'),
    ('tedious', 'Boring because it lasts too long.', 'A tedious wait at the airport.'),
    ('transparent', 'Open and easy to understand; hiding nothing.', 'A transparent hiring process.'),
    ('viable', 'Able to work successfully.', 'The plan is financially viable.'),
    ('vulnerable', 'Open to harm or attack.', 'The coast is vulnerable to flooding.'),
]


def create_starter_deck(apps, schema_editor):
    WordList = apps.get_model('vocab', 'WordList')
    Vocabulary = apps.get_model('vocab', 'Vocabulary')

    if WordList.objects.filter(share_code=STARTER_SHARE_CODE).exists():
        return

    word_list = WordList.objects.create(
        owner=None,
        name=STARTER_LIST_NAME,
        description='Common words that turn up everywhere in writing and exams.',
        file_name='starter-deck',
        share_code=STARTER_SHARE_CODE,
        is_public=True,
        total_words=len(STARTER_WORDS),
        words_processed=len(STARTER_WORDS),
        processing_status='completed',
    )

    Vocabulary.objects.bulk_create([
        Vocabulary(
            word_list=word_list,
            word=word,
            meaning_1=meaning,
            example_sentence=example,
        )
        for word, meaning, example in STARTER_WORDS
    ])


def remove_starter_deck(apps, schema_editor):
    WordList = apps.get_model('vocab', 'WordList')
    WordList.objects.filter(share_code=STARTER_SHARE_CODE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('vocab', '0008_vocabulary_audio_url_vocabulary_example_sentence_and_more'),
    ]

    operations = [
        migrations.RunPython(create_starter_deck, remove_starter_deck),
    ]
