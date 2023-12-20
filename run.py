# -*- encoding: utf-8 -*-
import os
import os.path as op
import sys

from pathlib import Path
from psychopy import core, visual

test = False

# make sure the experiment is on the PYTHONPATH
this_file = Path(__file__)
print(this_file)

if this_file == Path('run.py'):
    this_dir = os.getcwd()
    exp_dir = Path(this_dir)
    src_dir = Path(this_dir).parents[0]
    print(this_dir)
else:
    exp_dir = Path(__file__).parents[0]
    src_dir = Path(__file__).parents[1]

print(exp_dir)
print(src_dir)
sys.path = [str(exp_dir), str(src_dir)] + sys.path

from chainsaw.instructions import Instructions
from chainsaw.exp_utils import prepare_instructions
from exp import RefBackExp


def run(test=False):
    '''Run the experiment.'''
    exp = RefBackExp(exp_dir)

    lang = ['pl', 'eng'] if exp.settings['language'] == 'pl' else ['eng', 'pl']
    exp.get_subject_info(
        age=False, gender=True,
        additional={'language': lang, 'skip instructions': False,
                    'send_triggers': exp.send_triggers})

    window = visual.Window(
        monitor='testMonitor', units="height", fullscr=True)
    exp.set_window(window)
    exp.create_stimuli()

    # make sure there is a folder for the sounds
    sub = exp.subject['id']

    # run main
    exp.send_trigger(exp, exp.triggers['exp_start'])
    core.wait(0.05)

    # instructions?
    text_params = dict(height=0.045, units='height')
    gender_index = int(exp.subject['gender'] == 'male')
    pl_ending = ['owa', 'ów'][gender_index]
    this_msg = (rf'Jeśli jesteś got{pl_ending}, naciśnij dowolny przycisk.')
    exp.present_break(text=this_msg, text_params=text_params)

    # get ready slide
    block_n = 1
    exp.create_trials(block_n=block_n)
    exp.show_all_trials(subject_postfix=f'_block_{block_n}')

    # info - koniec treningu

    this_msg = ('To koniec części treningowej.\nInformacja zwrot'
                'na (kolorowe kółka) nie będzie już wyświetlana.')
    exp.present_break(text=this_msg, text_params=text_params)

    for block_n in range(2, 6):
        exp.create_trials(block_n=block_n)
        exp.show_all_trials(subject_postfix=f'_block_{block_n}',
                            feedback=False)
        exp.present_break(text=f'Koniec {block_n} z 5 części badania.',
                          text_params=text_params)

    # final thank you slide
    exp.present_break(text='Dziękujemy za udział w badaniu!',
                      text_params=text_params)

    # close the experiment
    core.quit()


if __name__ == '__main__':
    run(test=test)
