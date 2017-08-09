from __future__ import print_function

version = [0, 0, 2, 9, 7]

import warnings

import numpy as np

import scattertext.viz
from scattertext import SampleCorpora
from scattertext import Scalers, ScatterChart
from scattertext import termranking
from scattertext.AsianNLP import chinese_nlp, japanese_nlp
from scattertext.CSRMatrixTools import CSRMatrixFactory
from scattertext.CorpusFromPandas import CorpusFromPandas
from scattertext.CorpusFromParsedDocuments import CorpusFromParsedDocuments
from scattertext.IndexStore import IndexStore
from scattertext.ParsedCorpus import ParsedCorpus
from scattertext.Scalers import percentile_alphabetical
from scattertext.ScatterChart import ScatterChart
from scattertext.ScatterChartExplorer import ScatterChartExplorer
from scattertext.TermDocMatrix import TermDocMatrix
from scattertext.TermDocMatrixFactory import TermDocMatrixFactory, FeatsFromDoc
from scattertext.TermDocMatrixFilter import TermDocMatrixFilter, filter_bigrams_by_pmis
from scattertext.TermDocMatrixFromPandas import TermDocMatrixFromPandas
from scattertext.WhitespaceNLP import whitespace_nlp, whitespace_nlp_with_sentences, tweet_tokenzier_factory
from scattertext.features.FeatsFromOnlyEmpath import FeatsFromOnlyEmpath
from scattertext.features.FeatsFromSpacyDoc import FeatsFromSpacyDoc
from scattertext.features.FeatsFromSpacyDocAndEmpath import FeatsFromSpacyDocAndEmpath
from scattertext.features.FeatsFromSpacyDocOnlyEmoji import FeatsFromSpacyDocOnlyEmoji
from scattertext.features.FeatsFromSpacyDocOnlyNounChunks import FeatsFromSpacyDocOnlyNounChunks
from scattertext.representations.Word2VecFromParsedCorpus import Word2VecFromParsedCorpus, \
	Word2VecFromParsedCorpusBigrams
from scattertext.termranking import OncePerDocFrequencyRanker
from scattertext.termscoring.ScaledFScore import InvalidScalerException
from scattertext.termsignificance.LogOddsRatioUninformativeDirichletPrior import LogOddsRatioUninformativeDirichletPrior
from scattertext.viz import VizDataAdapter, HTMLVisualizationAssembly

def produce_scattertext_html(term_doc_matrix,
                             category,
                             category_name,
                             not_category_name,
                             protocol='https',
                             minimum_term_frequency=3,
                             pmi_threshold_coefficient=6,
                             max_terms=None,
                             filter_unigrams=False,
                             height_in_pixels=None,
                             width_in_pixels=None,
                             term_ranker=termranking.AbsoluteFrequencyRanker):
	'''Returns html code of visualization.

	Parameters
	----------
	term_doc_matrix : TermDocMatrix
		Corpus to use
	category : str
		name of category column
	category_name: str
		name of category to mine for
	not_category_name: str
		name of everything that isn't in category
	protocol : str
		optional, used prototcol of , http or https
	minimum_term_frequency : int, optional
		Minimum number of times word needs to appear to make it into visualization.
	pmi_threshold_coefficient : int, optional
		Filter out bigrams with a PMI of < 2 * pmi_threshold_coefficient. Default is 6.
	max_terms : int, optional
		Maximum number of terms to include in visualization.
	filter_unigrams : bool
		default False, do we filter unigrams that only occur in one bigram
	width_in_pixels: int
		width of viz in pixels, if None, default to JS's choice
	height_in_pixels: int
		height of viz in pixels, if None, default to JS's choice
	term_ranker : TermRanker
			TermRanker class for determining term frequency ranks.

	Returns
	-------
		str, html of visualization
	'''
	scatter_chart_data = ScatterChart(term_doc_matrix=term_doc_matrix,
	                                  minimum_term_frequency=minimum_term_frequency,
	                                  pmi_threshold_coefficient=pmi_threshold_coefficient,
	                                  filter_unigrams=filter_unigrams,
	                                  max_terms=max_terms,
	                                  term_ranker=term_ranker) \
		.to_dict(category=category,
	           category_name=category_name,
	           not_category_name=not_category_name,
	           transform=percentile_alphabetical)
	html = HTMLVisualizationAssembly(VizDataAdapter(scatter_chart_data),
	                                 width_in_pixels,
	                                 height_in_pixels).to_html(protocol=protocol)
	return html


def produce_scattertext_explorer(corpus,
                                 category,
                                 category_name,
                                 not_category_name,
                                 protocol='https',
                                 pmi_threshold_coefficient=6,
                                 minimum_term_frequency=3,
                                 minimum_not_category_term_frequency=0,
                                 max_terms=None,
                                 filter_unigrams=False,
                                 height_in_pixels=None,
                                 width_in_pixels=None,
                                 max_snippets=None,
                                 max_docs_per_category=None,
                                 metadata=None,
                                 scores=None,
                                 x_coords=None,
                                 y_coords=None,
                                 singleScoreMode=False,
                                 sort_by_dist=True,
                                 reverse_sort_scores_for_not_category=True,
                                 use_full_doc=False,
                                 transform=percentile_alphabetical,
                                 jitter=0,
                                 grey_zero_scores=False,
                                 term_ranker=None,
                                 asian_mode=False,
                                 use_non_text_features=False,
                                 show_characteristic=True,
                                 word_vec_use_p_vals=False,
                                 max_p_val=0.05,
                                 p_value_colors=False,
                                 term_significance=None,
                                 save_svg_button=False,
                                 x_label=None,
                                 y_label=None,
                                 d3_url=None,
                                 d3_scale_chromatic_url=None,
                                 pmi_filter_thresold=None,
                                 alternative_text_field=None):
	'''Returns html code of visualization.

	Parameters
	----------
	corpus : Corpus
		Corpus to use.
	category : str
		Name of category column as it appears in original data frame.
	category_name : str
		Name of category to use.  E.g., "5-star reviews."
	not_category_name : str
		Name of everything that isn't in category.  E.g., "Below 5-star reviews".
	protocol : str, optional
		Protocol to use.  Either http or https.  Default is https.
	pmi_threshold_coefficient : int, optional
		Filter out bigrams with a PMI of < 2 * pmi_threshold_coefficient. Default is 6
	minimum_term_frequency : int, optional
		Minimum number of times word needs to appear to make it into visualization.
	minimum_not_category_term_frequency : int, optional
	  If an n-gram does not occur in the category, minimum times it
	   must been seen to be included. Default is 0.
	max_terms : int, optional
		Maximum number of terms to include in visualization.
	filter_unigrams : bool, optional
		Default False, do we filter out unigrams that only occur in one bigram
	width_in_pixels : int, optional
		Width of viz in pixels, if None, default to JS's choice
	height_in_pixels : int, optional
		Height of viz in pixels, if None, default to JS's choice
	max_snippets : int, optional
		Maximum number of snippets to show when term is clicked.  If None, all are shown.
	max_docs_per_category: int, optional
		Maximum number of documents to store per category.  If None, by default, all are stored.
	metadata : list, optional
		list of meta data strings that will be included for each document
	scores : np.array, optional
		Array of term scores or None.
	x_coords : np.array, optional
		Array of term x-axis positions or None.  Must be in [0,1].
		If present, y_coords must also be present.
	y_coords : np.array, optional
		Array of term y-axis positions or None.  Must be in [0,1].
		If present, x_coords must also be present.
	singleScoreMode : bool, optional
		Label terms based on score vs distance from corner.  Good for topic scores. Show only one color.
	sort_by_dist: bool, optional
		Label terms based distance from corner. True by default.  Negated by singleScoreMode.
	reverse_sort_scores_for_not_category: bool, optional
		If using a custom score, score the not-category class by
		lowest-score-as-most-predictive. Turn this off for word vectory
		or topic similarity. Default True.
	use_full_doc : bool, optional
		Use the full document in snippets.  False by default.
	transform : function, optional
		not recommended for editing.  change the way terms are ranked.  default is st.Scalers.percentile_ordinal
	jitter : float, optional
		percentage of axis to jitter each point.  default is 0.
	grey_zero_scores : bool, optional
		If True, color points with zero-scores a light shade of grey.  False by default.
	term_ranker : TermRanker, optional
		TermRanker class for determining term frequency ranks.
	asian_mode : bool, optional
		Use a special Javascript regular expression that's specific to chinese or japanese
	use_non_text_features : bool, optional
		Show non-bag-of-words features (e.g., Empath) instaed of text.  False by default.
	show_characteristic: bool, default True
		Show characteristic terms on the far left-hand side of the visualization
	word_vec_use_p_vals: bool, default False
		Sort by harmonic mean of score and distance.
	max_p_val : float, default 0.05
		If word_vec_use_p_vals, the minimum p val to use.
	p_value_colors : bool, default False
	  Color points differently if p val is above 1-max_p_val, below max_p_val, or
	   in between.
	term_significance : TermSignifiance instance or None
		Way of getting signfiance scores.  If None, p values will not be added.
	save_svg_button : bool, default False
		Add a save as SVG button to the page.
	x_label : str, default None
		Custom x-axis label
	y_label : str, default None
		Custom y-axis label
	d3_url, str, None by default.  The url (or path) of d3.
		URL of d3, to be inserted into <script src="..."/>.  Overrides `protocol`.
	  By default, this is `DEFAULT_D3_URL` declared in `HTMLVisualizationAssembly`.
	d3_scale_chromatic_url, str, None by default.  Overrides `protocol`.
	  URL of d3 scale chromatic, to be inserted into <script src="..."/>
	  By default, this is `DEFAULT_D3_SCALE_CHROMATIC` declared in `HTMLVisualizationAssembly`.
	pmi_filter_thresold : (DEPRECATED) int, None by default
	  DEPRECATED.  Use pmi_threshold_coefficient instead.
	alternative_text_field : str or None, optional
		Field in from dataframe used to make corpus to display in place of parsed text. Only
		can be used if corpus is a ParsedCorpus instance.


	Returns
	-------
		str, html of visualization

	'''
	color = None
	if singleScoreMode or word_vec_use_p_vals:
		color = 'd3.interpolatePurples'
	if singleScoreMode or not sort_by_dist:
		sort_by_dist = False
	else:
		sort_by_dist = True
	if term_ranker is None:
		term_ranker = termranking.AbsoluteFrequencyRanker

	if pmi_filter_thresold is not None:
		pmi_threshold_coefficient = pmi_filter_thresold
		warnings.warn(
			"The argument name 'pmi_filter_thresold' has been deprecated. Use 'pmi_threshold_coefficient' in its place",
			DeprecationWarning)

	scatter_chart_explorer = ScatterChartExplorer(corpus,
	                                              minimum_term_frequency=minimum_term_frequency,
	                                              minimum_not_category_term_frequency=minimum_not_category_term_frequency,
	                                              pmi_threshold_coefficient=pmi_threshold_coefficient,
	                                              filter_unigrams=filter_unigrams,
	                                              jitter=jitter,
	                                              max_terms=max_terms,
	                                              term_ranker=term_ranker,
	                                              use_non_text_features=use_non_text_features,
	                                              term_significance=term_significance)
	if ((x_coords is None and y_coords is not None)
	    or (y_coords is None and x_coords is not None)):
		raise Exception("Both x_coords and y_coords need to be passed or both left blank")
	if x_coords is not None:
		scatter_chart_explorer.inject_coordinates(x_coords, y_coords)
	scatter_chart_data = scatter_chart_explorer.to_dict(category=category,
	                                                    category_name=category_name,
	                                                    not_category_name=not_category_name,
	                                                    transform=transform,
	                                                    scores=scores,
	                                                    max_docs_per_category=max_docs_per_category,
	                                                    metadata=metadata,
	                                                    alternative_text_field=alternative_text_field)
	return HTMLVisualizationAssembly(VizDataAdapter(scatter_chart_data),
	                                 width_in_pixels=width_in_pixels,
	                                 height_in_pixels=height_in_pixels,
	                                 max_snippets=max_snippets,
	                                 color=color,
	                                 grey_zero_scores=grey_zero_scores,
	                                 sort_by_dist=sort_by_dist,
	                                 reverse_sort_scores_for_not_category=reverse_sort_scores_for_not_category,
	                                 use_full_doc=use_full_doc,
	                                 asian_mode=asian_mode,
	                                 use_non_text_features=use_non_text_features,
	                                 show_characteristic=show_characteristic,
	                                 word_vec_use_p_vals=word_vec_use_p_vals,
	                                 max_p_val=max_p_val,
	                                 save_svg_button=save_svg_button,
	                                 p_value_colors=p_value_colors,
	                                 x_label=x_label,
	                                 y_label=y_label) \
		.to_html(protocol=protocol,
	           d3_url=d3_url,
	           d3_scale_chromatic_url=d3_scale_chromatic_url)


def word_similarity_explorer_gensim(corpus,
                                    category,
                                    category_name,
                                    not_category_name,
                                    target_term,
                                    word2vec=None,
                                    alpha=0.01,
                                    max_p_val=0.05,
                                    **kwargs):
	'''
		Parameters
		----------
		corpus : Corpus
			Corpus to use.
		category : str
			Name of category column as it appears in original data frame.
		category_name : str
			Name of category to use.  E.g., "5-star reviews."
		not_category_name : str
			Name of everything that isn't in category.  E.g., "Below 5-star reviews".
		target_term : str
			Word or phrase for semantic similarity comparison
		word2vec : word2vec.Word2Vec
		  Gensim-compatible Word2Vec model of lower-cased corpus. If none, o
		  ne will be trained using Word2VecFromParsedCorpus(corpus).train()
		alpha : float, default = 0.01
			Uniform dirichlet prior for p-value calculation
		max_p_val : float, default = 0.05
			Max p-val to use find set of terms for similarity calculation

		Remaining arguments are from `produce_scattertext_explorer`.
		Returns
		-------
			str, html of visualization
		'''

	if word2vec is None:
		word2vec = Word2VecFromParsedCorpus(corpus).train()

	scores = []

	for tok in corpus._term_idx_store._i2val:
		try:
			scores.append(word2vec.similarity(target_term, tok.replace(' ', '_')))
		except:
			try:
				scores.append(np.mean([word2vec.similarity(target_term, tok_part)
				                       for tok_part in tok.split()]))
			except:
				scores.append(0)
	scores = np.array(scores)

	return produce_scattertext_explorer(corpus,
	                                    category,
	                                    category_name,
	                                    not_category_name,
	                                    scores=scores,
	                                    sort_by_dist=False,
	                                    reverse_sort_scores_for_not_category=False,
	                                    word_vec_use_p_vals=True,
	                                    term_significance=LogOddsRatioUninformativeDirichletPrior(alpha),
	                                    max_p_val=max_p_val,
	                                    p_value_colors=True,
	                                    **kwargs)


def word_similarity_explorer(corpus,
                             category,
                             category_name,
                             not_category_name,
                             target_term,
                             nlp=None,
                             alpha=0.01,
                             max_p_val=0.05,
                             **kwargs):
	'''
	Parameters
	----------
	corpus : Corpus
		Corpus to use.
	category : str
		Name of category column as it appears in original data frame.
	category_name : str
		Name of category to use.  E.g., "5-star reviews."
	not_category_name : str
		Name of everything that isn't in category.  E.g., "Below 5-star reviews".
	target_term : str
		Word or phrase for semantic similarity comparison
	nlp : spaCy-like parsing function
		E.g., spacy.en.English, whitespace_nlp, etc...
	alpha : float, default = 0.01
		Uniform dirichlet prior for p-value calculation
	max_p_val : float, default = 0.05
		Max p-val to use find set of terms for similarity calculation
	Remaining arguments are from `produce_scattertext_explorer`.
	Returns
	-------
		str, html of visualization
	'''

	if nlp is None:
		import spacy
		nlp = spacy.en.English()

	base_term = nlp(target_term)
	scores = np.array([base_term.similarity(nlp(tok))
	                   for tok
	                   in corpus._term_idx_store._i2val])
	return produce_scattertext_explorer(corpus,
	                                    category,
	                                    category_name,
	                                    not_category_name,
	                                    scores=scores,
	                                    sort_by_dist=False,
	                                    reverse_sort_scores_for_not_category=False,
	                                    word_vec_use_p_vals=True,
	                                    term_significance=LogOddsRatioUninformativeDirichletPrior(alpha),
	                                    max_p_val=max_p_val,
	                                    p_value_colors=True,
	                                    **kwargs)


def sparse_explorer(corpus,
                    category,
                    category_name,
                    not_category_name,
                    scores,
                    **kwargs):
	'''
	Parameters
	----------
	corpus : Corpus
		Corpus to use.
	category : str
		Name of category column as it appears in original data frame.
	category_name : str
		Name of category to use.  E.g., "5-star reviews."
	not_category_name : str
		Name of everything that isn't in category.  E.g., "Below 5-star reviews".
	scores : np.array
		Scores to display in visualization.  Zero scores are grey.

	Remaining arguments are from `produce_scattertext_explorer`.

	Returns
	-------
		str, html of visualization
	'''

	return produce_scattertext_explorer(
		corpus,
		category,
		category_name,
		not_category_name,
		scores=scores,
		sort_by_dist=False,
		grey_zero_scores=True,
		**kwargs)
