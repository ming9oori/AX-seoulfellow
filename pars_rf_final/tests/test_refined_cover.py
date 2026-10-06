import unittest
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from kg_rag.refined_cover import candidate_union, sigmoid_logits, relevance_first_select, select_variant


class RefinedTests(unittest.TestCase):
    def test_union_all_aspects_no_three_cap(self):
        self.assertEqual(candidate_union(list("abcde"),[1,0,0,0,0],np.eye(5),question_k=1,aspect_k=1),[0,1,2,3,4])
    def test_one_aspect_equals_relevance(self):
        x=relevance_first_select(list("abc"),[.9,.8,.7],[[0,0,1]])
        self.assertEqual(x["evidence_ids"],list("abc"));self.assertEqual(x["effective_lambda"],1)
    def test_highest_relevance_always_first(self):
        x=relevance_first_select(list("abc"),[.9,.8,.1],[[0,0,1],[0,0,1]],K=2)
        self.assertEqual(x["evidence_ids"][0],"a")
    def test_complementary_gain(self):
        x=relevance_first_select(list("abc"),[.9,.8,.79],[[1,1,0],[0,0,1]],K=2,lam=.5)
        self.assertEqual(x["evidence_ids"],["a","c"])
    def test_sigmoid_extreme(self):
        self.assertTrue(np.allclose(sigmoid_logits([-1000,0,1000]),[0,.5,1]))
    def test_ties(self):
        x=relevance_first_select(["z","a"],[1,1],[[1,1]])
        self.assertEqual(x["evidence_ids"],["a","z"])
    def test_empty(self):
        self.assertEqual(relevance_first_select([],[],np.zeros((1,0)))["evidence_ids"],[])
    def test_invalid(self):
        with self.assertRaises(ValueError):sigmoid_logits([float('nan')])
        with self.assertRaises(ValueError):relevance_first_select(["a"],[1],np.zeros((0,1)))
    def test_ce_maps_ids(self):
        x=select_variant(list("abc"),[.9,.8,.7],[[1,1,1]],[2,0],[2,-2],"CE_TOP5")
        self.assertEqual(x["evidence_ids"],["c","a"])
    def test_bad_candidate_rejected(self):
        with self.assertRaises(ValueError):select_variant(["a"],[1],[[1]],[2],[1],"CE_TOP5")
    def test_more_than_three_aspects(self):
        x=relevance_first_select(list("abcd"),[.9,.8,.7,.6],np.eye(4))
        self.assertEqual(len(x["evidence_ids"]),4)
    def test_bound(self):
        x=relevance_first_select([str(i) for i in range(10)],np.ones(10),np.ones((2,10)))
        self.assertEqual(len(set(x["evidence_ids"])),5)


if __name__=="__main__":unittest.main()
