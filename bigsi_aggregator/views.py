import logging

from flask_restful import Resource
from flask_restful import fields, marshal_with, marshal
from flask_restful import reqparse

from bigsi_aggregator.helpers import BigsiAggregator
from bigsi_aggregator.models import SequenceSearch
from bigsi_aggregator.settings import BIGSI_URLS

logger = logging.getLogger(__name__)
from bigsi_aggregator.models import VariantSearch
from bigsi_aggregator import constants


bigsi_aggregator = BigsiAggregator(BIGSI_URLS)

seq_search_parser = reqparse.RequestParser()
seq_search_parser.add_argument("seq", type=str, help="The sequence query")
seq_search_parser.add_argument(
    "threshold", type=int, help="The percent k-mer presence result", default=100
)
seq_search_parser.add_argument(
    "score", type=bool, help="Score the search results", default=False
)


sequence_search_results_fields = {
    "sample_name": fields.String,
    "percent_kmers_found": fields.Integer,
    "num_kmers_found": fields.String,
    "num_kmers": fields.String,
    "score": fields.Float,
    "mismatches": fields.Float,
    "nident": fields.Float,
    "pident": fields.Float,
    "length": fields.Float,
    "evalue": fields.Float,
    "pvalue": fields.Float,
    "log_evalue": fields.Float,
    "log_pvalue": fields.Float,
    "kmer-presence": fields.String,
    # "metadata": fields.String,  ## In future, metadata associated with 'sampled_name' will be returned
}

sequence_search_fields = {
    "id": fields.String,
    constants.SEQUENCE_QUERY_KEY: fields.String,
    constants.THRESHOLD_KEY: fields.Integer,
    constants.SCORE_KEY: fields.Boolean,
    constants.COMPLETED_BIGSI_QUERIES_COUNT_KEY: fields.Integer,
    constants.TOTAL_BIGSI_QUERIES_COUNT_KEY: fields.Integer,
    constants.RESULTS_KEY: fields.Nested(sequence_search_results_fields),
    "status": fields.String,
    "citation": fields.String,
}


class SequenceSearchListResource(Resource):
    def post(self):
        args = seq_search_parser.parse_args()

        logger.info(self.post.__name__)
        logger.debug('args: %s', args)

        sequence_search = SequenceSearch.create(**args)
        if sequence_search.status is "PENDING":
            sequence_search.incr_request_queries()
            bigsi_aggregator.search_and_aggregate(sequence_search.id)
        return marshal(sequence_search, sequence_search_fields), 201


class SequenceSearchResource(Resource):
    @marshal_with(sequence_search_fields)
    def get(self, sequence_search_id):
        logger.info(self.get.__name__)
        logger.debug('sequence_search_id: %s', sequence_search_id)

        return SequenceSearch.get_by_id(sequence_search_id)


variant_search_parser = reqparse.RequestParser()
variant_search_parser.add_argument("reference", type=str, help="The reference filepath")
variant_search_parser.add_argument("ref", type=str, help="The ref base")
variant_search_parser.add_argument("pos", type=int, help="The variant position")
variant_search_parser.add_argument("alt", type=str, help="The alt base")
variant_search_parser.add_argument(
    "genbank", type=str, help="The genbank file", default=None
)
variant_search_parser.add_argument(
    "gene", type=str, help="The gene for amino acid queries", default=None
)


variant_search_results_fields = {
    "sample_name": fields.String,
    "genotype": fields.String,
    # "metadata": fields.String,  ## In future, metadata associated with 'sampled_name' will be returned
}

variant_search_fields = {
    "id": fields.String,
    constants.REFERENCE_KEY: fields.String,
    constants.REF_KEY: fields.String,
    constants.POS_KEY: fields.Integer,
    constants.ALT_KEY: fields.String,
    constants.GENBANK_KEY: fields.String,
    constants.GENE_KEY: fields.String,
    constants.COMPLETED_BIGSI_QUERIES_COUNT_KEY: fields.Integer,
    constants.TOTAL_BIGSI_QUERIES_COUNT_KEY: fields.Integer,
    constants.RESULTS_KEY: fields.Nested(variant_search_results_fields),
    "status": fields.String,
    "citation": fields.String,
}


class VariantSearchListResource(Resource):
    def post(self):
        args = variant_search_parser.parse_args()
        variant_search = VariantSearch.create(
            reference=args.reference,
            ref=args.ref,
            pos=args.pos,
            alt=args.alt,
            gene=args.gene,
            genbank=args.genbank,
        )
        if variant_search.status is "PENDING":
            variant_search.incr_request_queries()
            bigsi_aggregator.variant_search_and_aggregate(variant_search.id)
        return marshal(variant_search, variant_search_fields), 201


class VariantSearchResource(Resource):
    @marshal_with(variant_search_fields)
    def get(self, variant_search_id):
        return VariantSearch.get_by_id(variant_search_id)
