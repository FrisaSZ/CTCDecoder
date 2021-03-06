from __future__ import division
from __future__ import print_function
import numpy as np


class BeamEntry:
	"information about one single beam at specific time-step"
	def __init__(self):
		self.prTotal = 0 # blank and non-blank
		self.prNonBlank = 0 # non-blank
		self.prBlank = 0 # blank
		self.y = () # labeling at current time-step


class BeamState:
	"information about beams at specific time-step"
	def __init__(self):
		self.entries = {}

	def norm(self):
		"length-normalise probabilities to avoid penalising long labelings"
		for (k, _) in self.entries.items():
			labelingLen = len(self.entries[k].y)
			self.entries[k].prTotal = self.entries[k].prTotal ** (1.0 / (labelingLen if labelingLen else 1))

	def sort(self):
		"return beams sorted by probability"
		u = [v for (k, v) in self.entries.items()]
		s = sorted(u, reverse=True, key=lambda x: x.prTotal)
		return [x.y for x in s]


def calcExtPr(k, y, t, mat, beamState, lm, classes):
	"probability for extending labeling y to y+k"

	# language model (char bigrams)
	bigramProb = 1
	if lm:
		c1 = classes[y[-1] if y else classes.index(' ')]
		c2 = classes[k]
		lmFactor = 0.01 # controls influence of language model
		bigramProb = lm.getCharBigram(c1, c2) ** lmFactor

	# optical model (RNN)
	if y and y[-1] == k:
		return mat[t, k] * bigramProb*beamState.entries[y].prBlank
	return mat[t, k] * bigramProb * beamState.entries[y].prTotal


def addLabeling(beamState, y):
	"adds labeling if it does not exist yet"
	if y not in beamState.entries:
		beamState.entries[y] = BeamEntry()


def ctcBeamSearch(mat, classes, lm):
	"beam search similar to algorithm described by Hwang - Character-Level Incremental Speech Recognition with Recurrent Neural Networks"

	blankIdx = len(classes)
	maxT, maxC = mat.shape
	beamWidth = 25

	# Initialise beam state
	last = BeamState()
	y = ()
	last.entries[y] = BeamEntry()
	last.entries[y].prBlank = 1
	last.entries[y].prTotal = 1

	# go over all time-steps
	for t in range(maxT):
		curr = BeamState()

		# get best labelings
		BHat = last.sort()[0:beamWidth]

		# go over best labelings
		for y in BHat:
			prNonBlank = 0
			# if nonempty labeling
			if y:
				# seq prob so far and prob of seeing last label again
				prNonBlank = last.entries[y].prNonBlank * mat[t, y[-1]]

			# calc probabilities
			prBlank = (last.entries[y].prTotal) * mat[t, blankIdx]

			# save result
			addLabeling(curr, y)
			curr.entries[y].y = y
			curr.entries[y].prNonBlank += prNonBlank
			curr.entries[y].prBlank += prBlank
			curr.entries[y].prTotal += prBlank + prNonBlank

			# extend current labeling
			for k in range(maxC - 1):
				newY = y + (k,)
				prNonBlank = calcExtPr(k, y, t, mat, last, lm, classes)

				# save result
				addLabeling(curr, newY)
				curr.entries[newY].y = newY
				curr.entries[newY].prNonBlank += prNonBlank
				curr.entries[newY].prTotal += prNonBlank

		# set new beam state
		last = curr

	# normalise probabilities according to labeling length
	last.norm()

	 # sort by probability
	bestLabeling = last.sort()[0] # get most probable labeling

	# map labels to chars
	res = ''
	for l in bestLabeling:
		res += classes[l]

	return res


def testBeamSearch():
	"test decoder"
	classes = 'ab'
	mat = np.array([[0.4, 0, 0.6], [0.4, 0, 0.6]])
	print('Test beam search')
	expected = 'a'
	actual = ctcBeamSearch(mat, classes, None)
	print('Expected: "' + expected + '"')
	print('Actual: "' + actual + '"')
	print('OK' if expected == actual else 'ERROR')


if __name__ == '__main__':
	testBeamSearch()
