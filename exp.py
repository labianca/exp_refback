import os
import os.path as op
import numpy as np
import pandas as pd

from psychopy import visual, core, sound

from chainsaw.exp_utils import Experiment
from chainsaw.stim_utils import fix, feedback_circles
from chainsaw.io_utils import handle_responses, clear_buffer
from chainsaw import gentri_utils


def smart_square(window, width=0.2, height=0.2, color=None, lineWidth=0.05):
    """Create a better square than default visual.Rect object.

    The visual.Rect object does not take into account line width and
    creates a square that looks weird for thicker line widths."""

    hw = width / 2
    hh = height / 2
    lw = lineWidth
    # create positions, widths and heights for the 4 visual.Rect objects
    # constituting the four lines of the square
    pos = [[-hw, 0], [hw, 0], [0, hh], [0, -hh]]
    width = [lineWidth, lineWidth, width + lw, width + lw]
    height = [height + lw, height + lw, lineWidth, lineWidth]

    # create the 4 visual.Rect objects
    rects = [
        visual.Rect(window, pos=pos[idx], width=width[idx], height=height[idx],
                    fillColor=color, lineWidth=0)
        for idx in range(4)
    ]
    return rects


def create_stimuli(exp):
    stim = dict()

    # colors
    stim['pink'] = [0.436, -1., 0.436]
    stim['blue'] = [-0.368, -0.368, 0.982]

    # fixation
    fix_params = dict(height=0.02, units='height',
                      color=(0.85, 0.85, 0.85))
    stim['fix'] = fix(exp.window, **fix_params)

    # stimuli
    # we currently use X and O
    stim['stimuli'] = ['X', 'O']
    text_params = dict(height=0.12, units='height', color=(-1, -1, -1),
                       bold=True)

    for stim_name in stim['stimuli']:
        stim[stim_name] = visual.TextStim(
            exp.window, text=stim_name, **text_params)

    # reference frame
    box_params = dict(width=0.2, height=0.2, units='height', fillColor=None,
                      lineWidth=20)
    # lineColor,
    # stim['ref_True'] = visual.Rect(
    #     exp.window, lineColor=stim['pink'], **box_params)
    # stim['ref_False'] = visual.Rect(
    #     exp.window, lineColor=stim['blue'], **box_params)

    # create reference brackets using smart_square
    stim['ref_True'] = smart_square(exp.window, color=stim['pink'],
                                    lineWidth=0.025)
    stim['ref_False'] = smart_square(exp.window, color=stim['blue'],
                                     lineWidth=0.025)

    # feedback
    corr, incorr = feedback_circles(exp.window, radius=0.2, units='height')
    stim['feedback_correct'] = corr
    stim['feedback_incorrect'] = incorr

    exp.stim = stim


# The Experiment subclass has to define `.show_trial()` method
class RefBackExp(Experiment):
    def __init__(self, base_dir):
        super().__init__(base_dir)

    def create_stimuli(self):
        create_stimuli(self)

    def create_trials(self, block_n=1, trial_start=1):
        # this should just read trials from disk
        df = create_block_dataframe()
        df.loc[:, 'block'] = block_n
        tri_num = np.arange(len(df)) + trial_start
        df.loc[:, 'trial'] = tri_num
        columns = ['trial', 'block'] + df.columns.tolist()[:-2]
        df = df[columns]
        self.trials = df
        self.reset_beh()

    def show_trial(self, trial_info, feedback=True):
        # each trial started with a fixation screen that was presented for
        # 800 ms, followed by a blank display for 1,000 ms. Then, one of the
        # stimuli “X” or “O” was selected at random and presented until a
        # response was indicated
        # (but first REF trial does not require a response?)

        # setup
        # -----
        trial_idx = trial_info.name

        # compose stimulus:
        # -----------------
        stim_idx = trial_info.stim
        is_ref = trial_info.reference
        letter = self.stim['stimuli'][stim_idx]
        ref_frame = f'ref_{is_ref}'
        show_stim = self.stim[ref_frame] + [self.stim[letter]]
        stim_trigger = 10 + stim_idx + 2 * is_ref

        # times
        blank_time = self.get_time('blank')

        # present
        # -------
        # record time at the start of the trial
        self.beh.loc[self.current_loc, 'time_start'] = self.exp_clock.getTime()
        self.beh.loc[self.current_loc, 'feedback'] = feedback

        # show fixation
        self.show_element('fix')

        # blank screen
        self.show_element('', time=blank_time)

        # show stimulus and await response
        clear_buffer(device=self.response_device)
        key, rt = self.show_element(show_stim, time=np.inf, reset_clock=True,
                                    await_response=True, trigger=stim_trigger)

        # record time at the trial end
        self.beh.loc[self.current_loc, 'time_end'] = self.exp_clock.getTime()

        if trial_info.trial == 1:
            correct_action = ['yes', 'no']
        else:
            correct_action = ['no', 'yes'][int(trial_info.is_same)]
        key, ifcorrect, rt = handle_responses(
            self, correct_resp=correct_action, key=key, rt=rt)

        if feedback:
            fdb_name = 'feedback_' + ('correct' if ifcorrect else 'incorrect')
            feedback_time = self.get_time('feedback')
            self.show_element('', self.get_time('pre_feedback'))
            self.show_element(fdb_name, feedback_time)

        # test quit button
        print(key)
        self.check_quit(key=key)


def generate_ref_back_block(n_trials=60):
    stims = np.array([0, 1])
    stream = np.random.choice(stims, size=60)
    ref_stream = create_ref_stream(n_trials=n_trials)
    return stream, ref_stream


def create_ref_stream(n_trials=60, same_prop_wanted=0.75, n_rep=10_000):
    use_stream = np.random.choice([False, True], size=60)
    current_prop = (use_stream[:-1] == use_stream[1:]).mean()
    current_diff = np.abs(same_prop_wanted - current_prop)

    n_pairs = n_trials - 1
    n_same_pairs = int(np.round(same_prop_wanted * n_pairs))
    closest_possible = n_same_pairs / n_pairs

    for idx in range(10_000):
        ref_stream = np.random.choice([False, True], size=60)
        ref_stream[0] = True  # always starts with a reference
        same_prop = (ref_stream[:-1] == ref_stream[1:]).mean()
        diff = np.abs(same_prop_wanted - same_prop)
        if diff < current_diff:
            use_stream = ref_stream
            current_prop = same_prop
            current_diff = diff

            if current_prop == closest_possible:
                return np.array(use_stream)
    return np.array(use_stream)


def parse_ref_back_block(stream, ref_stream):
    assert ref_stream[0]
    current_in_mem = stream[0]
    in_mem = [current_in_mem]
    is_same = [False]

    for st, ref in zip(stream[1:], ref_stream[1:]):
        in_mem.append(current_in_mem)
        is_same.append(current_in_mem == st)

        if ref:
            current_in_mem = st

    return is_same, in_mem


def create_block_dataframe():

    stream, ref_stream = generate_ref_back_block()
    is_same, in_mem = parse_ref_back_block(stream, ref_stream)

    df = pd.DataFrame({'stim': stream, 'reference': ref_stream,
                       'is_same': is_same, 'in_mem': in_mem})
    return df
