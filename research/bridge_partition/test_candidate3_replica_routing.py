#!/usr/bin/env python3
"""Fast exhaustive checks for 4-shard replicated/fragmented routing semantics.

Proof-backed properties are NOT claimed as algorithmic novelties.
"""
import itertools, unittest
from candidate3_byte_matched_replication import span

class ExactFourShardCover(unittest.TestCase):
    def test_replication_cannot_increase_routed_shards(self):
        # Every possible 6-predicate query with 2..5 predicates; fixed 4-shard layout.
        route={f"p{i}":{i%4} for i in range(6)}
        fragments=set()
        for n in range(2,6):
            for q in itertools.combinations(sorted(route),n):
                before=span(route,q,fragments)
                for key in route:
                    for dst in range(4):
                        newer={k:set(v) for k,v in route.items()}
                        newer[key].add(dst)
                        after=span(newer,q,fragments)
                        self.assertLessEqual(after,before)
    def test_fragmented_data_requires_all_owners(self):
        route={"fragment":{0,1,2},"other":{3},"rep":{0,3}}
        fragmented={"fragment"}
        self.assertEqual(span(route,("fragment",),fragmented),3)
        self.assertEqual(span(route,("fragment","other"),fragmented),4)
        self.assertEqual(span(route,("rep","other"),fragmented),1)
        self.assertEqual(span(route,("fragment","rep"),fragmented),3)
    def test_move_can_harm_some_future_query_even_if_others_gain(self):
        original={"a":{0},"b":{0},"c":{1},"d":{1}}
        updated={"a":{1},"b":{0},"c":{0},"d":{1}}
        self.assertEqual(span(original,("a","b"),set()),1)
        self.assertEqual(span(updated,("a","b"),set()),2)
        self.assertEqual(span(original,("a","d"),set()),2)
        self.assertEqual(span(updated,("a","d"),set()),1)

if __name__=="__main__":unittest.main(verbosity=2)
