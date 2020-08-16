# Author: Simon Blanke
# Email: simon.blanke@yahoo.com
# License: MIT License


import numpy as np

from sklearn.neighbors import KernelDensity

from .sbom import SBOM


class TreeStructuredParzenEstimators(SBOM):
    def __init__(self, space_dim, gamma_tpe=0.3):
        super().__init__(space_dim)
        self.gamma_tpe = gamma_tpe

        self.kd_best = KernelDensity()
        self.kd_worst = KernelDensity()

    def _get_samples(self):
        n_samples = len(self.X_sample)

        n_best = int(n_samples * self.gamma_tpe)

        Y_sample = np.array(self.Y_sample)
        index_best = Y_sample.argsort()[-n_best:][::-1]

        best_samples = [self.X_sample[i] for i in index_best]
        worst_samples = [self.X_sample[i] for i in ~index_best]

        return best_samples, worst_samples

    def expected_improvement(self):
        logprob_best = self.kd_best.score_samples(self.all_pos_comb)
        logprob_worst = self.kd_worst.score_samples(self.all_pos_comb)

        prob_best = np.exp(logprob_best)
        prob_worst = np.exp(logprob_worst)

        return np.divide(
            prob_best, prob_worst, out=np.zeros_like(prob_worst), where=prob_worst != 0
        )

    def propose_location(self):
        best_samples, worst_samples = self._get_samples()

        self.kd_best.fit(best_samples)
        self.kd_worst.fit(worst_samples)

        exp_imp = self.expected_improvement()
        index_best = list(exp_imp.argsort()[::-1])

        all_pos_comb_sorted = self.all_pos_comb[index_best]
        pos_best = all_pos_comb_sorted[0]

        return pos_best

    def iterate(self, nth_iter):

        if nth_iter < self.start_up_evals:
            pos = self.move_random()
        else:
            pos = self.propose_location()
            self.pos_new = pos

        self.X_sample.append(pos)

        return pos

    def evaluate(self, score_new):
        self.score_new = score_new

        self._evaluate_new2current(score_new)
        self._evaluate_current2best()

        self.Y_sample.append(score_new)

