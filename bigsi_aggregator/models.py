import redis
import json
from bigsi_aggregator import constants
from bigsi_aggregator.settings import REDIS_IP

import hashlib

DEFAULT_SEARCH_RESULTS_TTL = 48 * 60 * 60  # 2 days
r = redis.StrictRedis(REDIS_IP, decode_responses=True)


class BaseSearch:
    def __init__(
        self,
        total_bigsi_queries,
        results=[],
        completed_bigsi_queries=0,
        ttl=DEFAULT_SEARCH_RESULTS_TTL,
    ):
        self.total_bigsi_queries = total_bigsi_queries
        self._id = self.generate_id()
        self.ttl = ttl
        self.completed_bigsi_queries = completed_bigsi_queries
        self.results = results
        self.citation = "http://dx.doi.org/10.1038/s41587-018-0010-1"

    @property
    def search_key(self):
        return self.generate_search_key(self.id)

    @property
    def id(self):
        return self._id

    @classmethod
    def get_by_id(cls, _id):
        search_params = r.hgetall(cls.generate_search_key(_id))
        results = r.hgetall(cls.generate_search_results_key(_id))
        results = [json.loads(s) for s in results.values()]
        sequence_search = cls(**search_params, results=results)
        sequence_search.set_ttl()
        return sequence_search

    @property
    def in_progress(self):
        return self.completed_bigsi_queries < self.total_bigsi_queries

    @property
    def search_results_key(self):
        return self.generate_search_results_key(self.id)

    @property
    def status(self):
        if self.completed_bigsi_queries < self.total_bigsi_queries:
            return "INPROGRESS"
        else:
            return "COMPLETE"

    def set_ttl(self, ttl=DEFAULT_SEARCH_RESULTS_TTL):
        r.expire(self.search_results_key, ttl)
        r.expire(self.search_key, ttl)

    def progress(self):
        return self.completed_bigsi_queries / self.total_bigsi_queries

    def add_results(self, results):
        search_results_key = self.generate_search_results_key(self.id)
        for res in results:
            r.hset(self.search_results_key, res["sample_name"], json.dumps(res))
        self.incr_completed_queries()
        self.set_ttl()

    def incr_completed_queries(self):
        r.hincrby(self.search_key, constants.COMPLETED_BIGSI_QUERIES_COUNT_KEY, 1)


class SequenceSearch(BaseSearch):
    def __init__(
        self,
        seq,
        threshold,
        score,
        total_bigsi_queries,
        results=[],
        completed_bigsi_queries=0,
        ttl=DEFAULT_SEARCH_RESULTS_TTL,
    ):
        self.seq = seq
        self.threshold = threshold
        self.score = bool(int(score))
        super(SequenceSearch, self).__init__(
            total_bigsi_queries, results, completed_bigsi_queries, ttl
        )

    @classmethod
    def generate_search_key(cls, _id):
        return "sequence_search:%s" % _id

    @classmethod
    def generate_search_results_key(cls, _id):
        return "sequence_search_results:%s" % _id

    @classmethod
    def create(cls, seq, threshold, score, total_bigsi_queries):
        sequence_search = cls(seq, threshold, score, total_bigsi_queries)
        if r.exists(cls.generate_search_key(sequence_search.id)):
            return cls.get_by_id(sequence_search.id)
        else:
            sequence_search.create_cache()
            sequence_search.set_ttl()
        return sequence_search

    def __dict__(self):
        return {
            constants.SEQUENCE_QUERY_KEY: self.seq,
            constants.THRESHOLD_KEY: self.threshold,
            constants.SCORE_KEY: self.score,
            constants.COMPLETED_BIGSI_QUERIES_COUNT_KEY: self.completed_bigsi_queries,
            constants.TOTAL_BIGSI_QUERIES_COUNT_KEY: self.total_bigsi_queries,
            constants.RESULTS_KEY: self.results,
        }

    def create_cache(self):
        search_params_key = self.generate_search_key(self.id)
        r.hset(search_params_key, constants.SEQUENCE_QUERY_KEY, self.seq)
        r.hset(search_params_key, constants.THRESHOLD_KEY, self.threshold)
        r.hset(search_params_key, constants.SCORE_KEY, int(self.score))
        r.hset(search_params_key, constants.COMPLETED_BIGSI_QUERIES_COUNT_KEY, 0)
        r.hset(
            search_params_key,
            constants.TOTAL_BIGSI_QUERIES_COUNT_KEY,
            self.total_bigsi_queries,
        )

    def generate_id(self):
        string = "{seq}{threshold}{score}{total_bigsi_queries}".format(
            seq=self.seq,
            threshold=self.threshold,
            score=int(self.score),
            total_bigsi_queries=self.total_bigsi_queries,
        )
        _hash = hashlib.sha224(string.encode("utf-8")).hexdigest()[:24]
        return _hash


class VariantSearch(BaseSearch):
    def __init__(
        self,
        reference,
        ref,
        pos,
        alt,
        gene=None,
        genbank=None,
        results=[],
        completed_bigsi_queries=0,
        ttl=DEFAULT_SEARCH_RESULTS_TTL,
        total_bigsi_queries=1,
    ):

        self.reference = reference
        self.ref = ref
        self.pos = pos
        self.alt = alt
        self.gene = gene
        self.genbank = genbank
        super(VariantSearch, self).__init__(
            total_bigsi_queries, results, completed_bigsi_queries, ttl
        )

    @classmethod
    def create(cls, reference, ref, pos, alt, gene, genbank, total_bigsi_queries):
        variant_search = cls(
            reference, ref, pos, alt, gene, genbank, total_bigsi_queries
        )
        if r.exists(cls.generate_search_key(variant_search.id)):
            return cls.get_by_id(variant_search.id)
        else:
            variant_search.create_cache()
            variant_search.set_ttl()
        return variant_search

    @classmethod
    def generate_search_key(cls, _id):
        return "variant_search:%s" % _id

    @classmethod
    def generate_search_results_key(cls, _id):
        return "variant_search_results:%s" % _id

    def __dict__(self):
        return {
            constants.REFERENCE_KEY: self.reference,
            constants.REF_KEY: self.ref,
            constants.POS_KEY: self.pos,
            constants.ALT_KEY: self.alt,
            constants.GENBANK_KEY: self.genbank,
            constants.GENE_KEY: self.gene,
            constants.COMPLETED_BIGSI_QUERIES_COUNT_KEY: self.completed_bigsi_queries,
            constants.TOTAL_BIGSI_QUERIES_COUNT_KEY: self.total_bigsi_queries,
            constants.RESULTS_KEY: self.results,
        }

    def generate_id(self):
        string = "{reference}{ref}{pos}{alt}{gene}{genbank}{total_bigsi_queries}".format(
            reference=self.reference,
            ref=self.ref,
            pos=self.pos,
            alt=self.alt,
            gene=self.gene,
            genbank=self.genbank,
            total_bigsi_queries=self.total_bigsi_queries,
        )
        _hash = hashlib.sha224(string.encode("utf-8")).hexdigest()[:24]
        return _hash

    def create_cache(self):
        search_params_key = self.generate_search_key(self.id)

        r.hset(search_params_key, constants.COMPLETED_BIGSI_QUERIES_COUNT_KEY, 0)
        r.hset(
            search_params_key,
            constants.TOTAL_BIGSI_QUERIES_COUNT_KEY,
            self.total_bigsi_queries,
        )

        r.hset(search_params_key, constants.REFERENCE_KEY, self.reference)
        r.hset(search_params_key, constants.REF_KEY, self.ref)
        r.hset(search_params_key, constants.POS_KEY, self.pos)
        r.hset(search_params_key, constants.ALT_KEY, self.alt)
        if self.gene:
            r.hset(search_params_key, constants.GENE_KEY, self.gene)
        if self.genbank:
            r.hset(search_params_key, constants.GENBANK_KEY, self.genbank)
