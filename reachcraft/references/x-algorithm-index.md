# X Algorithm Index For ReachCraft

Snapshot indexed locally from `https://github.com/xai-org/x-algorithm` on 2026-05-17.

- Commit: `0bfc2795d308f90032544322747caacd535f75ae`
- Latest commit date in clone: 2026-05-15 21:54:59 +0000
- License: Apache-2.0
- Files indexed, excluding `.git`: 216
- Major directories: `home-mixer` 118 files, `grox` 59 files, `phoenix` 13 files, `thunder` 11 files, `candidate-pipeline` 10 files

Use this reference to translate the public code into practical posting advice. Do not claim exact production weights or guaranteed reach.

## Feed Pipeline

The public release describes the For You feed as:

1. Hydrate the viewer query with recent user actions, followed accounts, muted/blocked accounts, topics, demographics, served history, impression filters, and other context.
2. Source candidates from in-network accounts, out-of-network retrieval, topic retrieval, cached posts, and other sources.
3. Hydrate candidates with text, author info, quote/reply/retweet data, media/video data, language, engagement counts, topic tags, safety labels, subscription data, mutual-follow data, and visibility data.
4. Filter ineligible or low-fit candidates.
5. Score with Phoenix predictions and ranking logic.
6. Apply author diversity and out-of-network weighting.
7. Select top candidates and run final visibility/conversation filters.

## Main Components

- `home-mixer`: Orchestrates For You feed candidate sourcing, hydration, filtering, scoring, selection, and side effects.
- `phoenix`: Two-stage recommendation model. Retrieval narrows candidates with user/post embeddings. Ranking predicts per-action engagement probabilities.
- `thunder`: In-network recent post store for accounts the viewer follows. Default post store retention is two days in `PostStore::default`.
- `grox`: Content understanding pipeline for safety, spam, reply ranking, post embeddings, summaries, multimodal analysis, and "banger" quality scoring.
- `candidate-pipeline`: Generic Rust traits for source, hydrator, filter, scorer, selector, and side effect stages.

## Positive Engagement Signals

Phoenix exposes predictions for:

- favorite/like
- reply
- repost
- photo expand
- click
- profile click
- video quality view (`vqv`)
- share
- share via DM
- share via copy link
- dwell
- quote
- quoted click
- follow author
- continuous dwell time
- click dwell time in newer ranking code

Practical translation:

- Write for a portfolio of actions, not just likes.
- Use hooks and structure for dwell.
- Add useful specificity that makes replies and reposts natural.
- Make profile promise strong, because profile clicks and follow-author predictions exist.
- Use screenshots, diagrams, demos, or video when they increase inspection, clarity, or proof.
- Give people a reason to share privately or copy a link: templates, checklists, sharp insight, useful resource, or surprising build result.

## Negative Feedback Signals

The ranking code includes negative predictions for:

- not interested
- block author
- mute author
- report
- not dwelled in newer ranking code

Practical translation:

- Avoid misleading claims, shallow bait, repetitive posting, harassment, polarizing rage bait, and low-effort replies.
- Do not post content that earns curiosity clicks but quick disappointment.
- Avoid broad generic posts when a sharper niche version would attract the right audience and repel fewer people.

## Scoring Notes

`home-mixer/scorers/ranking_scorer.rs` combines predicted actions with feature-switch weights. The exact production values are not in the public release.

`phoenix/run_pipeline.py` includes a demo scoring formula:

- favorite: `1.0`
- reply: `0.5`
- repost: `0.3`
- dwell: `0.2`

Use those demo values only as intuition: likes matter, but replies, reposts, and dwell are still explicit ranking ingredients. Production scoring can differ.

## Candidate Sources And What They Mean For Creators

- In-network (`ThunderSource`): posts from accounts a viewer follows. Build mutual relevance and follower quality, because followers are a direct candidate path.
- Out-of-network (`PhoenixSource`): posts discovered through user action history and embeddings. Make posts semantically clear and topic-consistent so they can be retrieved for the right users.
- Topic retrieval (`PhoenixTopicsSource`): topic entities can influence retrieval. Keep topic language explicit enough for classification.
- Cached posts and mixer sources: repeated serving history matters. Do not rely on reposting the same idea unchanged.

## Important Filters

Home Mixer filters include duplicates, old posts, self posts, retweet deduplication, ineligible subscriptions, previously seen posts, previously served posts, muted keywords, author social graph restrictions, video exclusion requests, topic inclusion/exclusion, visibility filtering, ancillary visibility filtering, and conversation deduplication.

Practical translation:

- Recency helps, especially for in-network sourcing.
- Avoid near-duplicate posts and repeated threads.
- Do not overuse muted or spammy keywords.
- Make each post stand alone while fitting a clear topic lane.
- Avoid content that triggers visibility or safety filters.

## Author Diversity

Ranking applies an author diversity multiplier so repeated posts from the same author in one response are attenuated.

Practical translation:

- Do not expect a burst of many similar posts to occupy a feed.
- Post consistently across time, not as a same-minute flood.
- Use replies and quote posts to participate across conversations instead of only broadcasting.

## Reply Ranking And Replies

Grox includes reply ranking and spam comment classification. Reply ranking targets replies on higher-blast-radius conversations, while low-follower reply spam is screened separately.

Practical translation:

- Reply thoughtfully to larger or highly relevant accounts.
- Add context, proof, disagreement with reasons, or useful examples.
- Avoid "great post", generic promo drops, repeated templates, or off-topic links.

## Content Understanding

Grox includes:

- `banger_initial_screen`: quality score, description, tags, taxonomy categories, high-quality metadata, image editability, slop score, minor score.
- spam comment classification.
- safety/PTOS classifiers.
- multimodal post embeddings.
- post summaries for embeddings.
- reply-specific embeddings and ranking.

Practical translation:

- Make the post easy for a model and human to summarize.
- Put the core claim early.
- Use media that reinforces the text.
- Avoid AI-slop texture: vague superlatives, generic inspiration, no proof, no concrete artifact.

## Profile Signals

Candidate data includes author screen name, author follower count, profile click prediction, follow-author prediction, mutual follow data, and author-blocks-viewer checks.

Practical translation:

- A clear bio, pinned post, and consistent account promise make profile clicks convert.
- Small accounts need trust-dense posts: proof, build logs, screenshots, lessons, and direct usefulness.
- Mutual-follow and in-network paths make community participation valuable.

## Source Inventory

Top-level and representative indexed files:

- `README.md`
- `LICENSE`
- `CODE_OF_CONDUCT.md`
- `candidate-pipeline/candidate_pipeline.rs`
- `candidate-pipeline/filter.rs`
- `candidate-pipeline/hydrator.rs`
- `candidate-pipeline/lib.rs`
- `candidate-pipeline/query_hydrator.rs`
- `candidate-pipeline/scorer.rs`
- `candidate-pipeline/selector.rs`
- `candidate-pipeline/side_effect.rs`
- `candidate-pipeline/source.rs`
- `candidate-pipeline/util.rs`
- `home-mixer/candidate_hydrators/ads_brand_safety_hydrator.rs`
- `home-mixer/candidate_hydrators/ads_brand_safety_vf_hydrator.rs`
- `home-mixer/candidate_hydrators/blocked_by_hydrator.rs`
- `home-mixer/candidate_hydrators/core_data_candidate_hydrator.rs`
- `home-mixer/candidate_hydrators/engagement_counts_hydrator.rs`
- `home-mixer/candidate_hydrators/filtered_topics_hydrator.rs`
- `home-mixer/candidate_hydrators/following_replied_users_hydrator.rs`
- `home-mixer/candidate_hydrators/gizmoduck_hydrator.rs`
- `home-mixer/candidate_hydrators/has_media_hydrator.rs`
- `home-mixer/candidate_hydrators/in_network_candidate_hydrator.rs`
- `home-mixer/candidate_hydrators/language_code_hydrator.rs`
- `home-mixer/candidate_hydrators/mod.rs`
- `home-mixer/candidate_hydrators/mutual_follow_jaccard_hydrator.rs`
- `home-mixer/candidate_hydrators/quote_hydrator.rs`
- `home-mixer/candidate_hydrators/subscription_hydrator.rs`
- `home-mixer/candidate_hydrators/tweet_type_metrics_hydrator.rs`
- `home-mixer/candidate_hydrators/vf_candidate_hydrator.rs`
- `home-mixer/candidate_hydrators/video_duration_candidate_hydrator.rs`
- `home-mixer/candidate_pipeline/candidate.rs`
- `home-mixer/candidate_pipeline/candidate_features.rs`
- `home-mixer/candidate_pipeline/for_you_candidate_pipeline.rs`
- `home-mixer/candidate_pipeline/mod.rs`
- `home-mixer/candidate_pipeline/phoenix_candidate_pipeline.rs`
- `home-mixer/candidate_pipeline/query.rs`
- `home-mixer/candidate_pipeline/query_features.rs`
- `home-mixer/filters/age_filter.rs`
- `home-mixer/filters/ancillary_vf_filter.rs`
- `home-mixer/filters/author_socialgraph_filter.rs`
- `home-mixer/filters/core_data_hydration_filter.rs`
- `home-mixer/filters/dedup_conversation_filter.rs`
- `home-mixer/filters/drop_duplicates_filter.rs`
- `home-mixer/filters/ineligible_subscription_filter.rs`
- `home-mixer/filters/mod.rs`
- `home-mixer/filters/muted_keyword_filter.rs`
- `home-mixer/filters/new_user_topic_ids_filter.rs`
- `home-mixer/filters/previously_seen_posts_backup_filter.rs`
- `home-mixer/filters/previously_seen_posts_filter.rs`
- `home-mixer/filters/previously_served_posts_filter.rs`
- `home-mixer/filters/retweet_deduplication_filter.rs`
- `home-mixer/filters/self_tweet_filter.rs`
- `home-mixer/filters/topic_ids_filter.rs`
- `home-mixer/filters/vf_filter.rs`
- `home-mixer/filters/video_filter.rs`
- `home-mixer/models/brand_safety.rs`
- `home-mixer/models/candidate.rs`
- `home-mixer/models/candidate_features.rs`
- `home-mixer/models/in_network_reply.rs`
- `home-mixer/models/mod.rs`
- `home-mixer/models/query.rs`
- `home-mixer/models/user_features.rs`
- `home-mixer/query_hydrators/blocked_user_ids_query_hydrator.rs`
- `home-mixer/query_hydrators/cached_posts_query_hydrator.rs`
- `home-mixer/query_hydrators/followed_grok_topics_query_hydrator.rs`
- `home-mixer/query_hydrators/followed_starter_packs_query_hydrator.rs`
- `home-mixer/query_hydrators/followed_user_ids_query_hydrator.rs`
- `home-mixer/query_hydrators/impressed_posts_query_hydrator.rs`
- `home-mixer/query_hydrators/impression_bloom_filter_query_hydrator.rs`
- `home-mixer/query_hydrators/inferred_grok_topics_query_hydrator.rs`
- `home-mixer/query_hydrators/ip_query_hydrator.rs`
- `home-mixer/query_hydrators/mod.rs`
- `home-mixer/query_hydrators/muted_user_ids_query_hydrator.rs`
- `home-mixer/query_hydrators/mutual_follow_query_hydrator.rs`
- `home-mixer/query_hydrators/past_request_timestamps_query_hydrator.rs`
- `home-mixer/query_hydrators/retrieval_sequence_query_hydrator.rs`
- `home-mixer/query_hydrators/scoring_sequence_query_hydrator.rs`
- `home-mixer/query_hydrators/served_history_query_hydrator.rs`
- `home-mixer/query_hydrators/subscribed_user_ids_query_hydrator.rs`
- `home-mixer/query_hydrators/user_action_seq_query_hydrator.rs`
- `home-mixer/query_hydrators/user_demographics_query_hydrator.rs`
- `home-mixer/query_hydrators/user_features_query_hydrator.rs`
- `home-mixer/query_hydrators/user_inferred_gender_query_hydrator.rs`
- `home-mixer/scorers/author_diversity_scorer.rs`
- `home-mixer/scorers/oon_scorer.rs`
- `home-mixer/scorers/phoenix_scorer.rs`
- `home-mixer/scorers/ranking_scorer.rs`
- `home-mixer/scorers/vm_ranker.rs`
- `home-mixer/scorers/weighted_scorer.rs`
- `home-mixer/selectors/blender_selector.rs`
- `home-mixer/selectors/top_k_score_selector.rs`
- `home-mixer/sources/ads_source.rs`
- `home-mixer/sources/cached_posts_source.rs`
- `home-mixer/sources/phoenix_moe_source.rs`
- `home-mixer/sources/phoenix_source.rs`
- `home-mixer/sources/phoenix_topics_source.rs`
- `home-mixer/sources/prompts_source.rs`
- `home-mixer/sources/push_to_home_source.rs`
- `home-mixer/sources/scored_posts_source.rs`
- `home-mixer/sources/thunder_source.rs`
- `home-mixer/sources/tweet_mixer_source.rs`
- `home-mixer/sources/who_to_follow_source.rs`
- `home-mixer/side_effects/cache_request_info_side_effect.rs`
- `home-mixer/side_effects/client_events_kafka_side_effect.rs`
- `home-mixer/side_effects/for_you_response_stats_side_effect.rs`
- `home-mixer/side_effects/mutual_follow_stats_side_effect.rs`
- `home-mixer/side_effects/phoenix_experiments_side_effect.rs`
- `home-mixer/side_effects/phoenix_request_cache_side_effect.rs`
- `home-mixer/side_effects/publish_seen_ids_to_kafka_side_effect.rs`
- `home-mixer/side_effects/redis_post_candidate_cache_side_effect.rs`
- `home-mixer/side_effects/reranking_kafka_side_effect.rs`
- `home-mixer/side_effects/scored_stats_side_effect.rs`
- `home-mixer/side_effects/served_candidates_kafka_side_effect.rs`
- `home-mixer/side_effects/truncate_served_history_side_effect.rs`
- `home-mixer/side_effects/update_past_request_timestamps_side_effect.rs`
- `home-mixer/side_effects/update_served_history_side_effect.rs`
- `home-mixer/for_you_server.rs`
- `home-mixer/scored_posts_server.rs`
- `home-mixer/server.rs`
- `grox/classifiers/content/banger_initial_screen.py`
- `grox/classifiers/content/classifier.py`
- `grox/classifiers/content/post_safety_screen_deluxe.py`
- `grox/classifiers/content/reply_ranking.py`
- `grox/classifiers/content/safety_ptos.py`
- `grox/classifiers/content/spam.py`
- `grox/data_loaders/asr_processor.py`
- `grox/data_loaders/kafka_loader.py`
- `grox/data_loaders/message_queue_loader.py`
- `grox/data_loaders/strato_loader.py`
- `grox/embedder/multimodal_post_embedder_v2.py`
- `grox/embedder/multimodal_post_embedder_v5.py`
- `grox/plans/plan_initial_banger.py`
- `grox/plans/plan_master.py`
- `grox/plans/plan_post_embedding_v5.py`
- `grox/plans/plan_post_embedding_v5_for_reply.py`
- `grox/plans/plan_post_embedding_with_summary.py`
- `grox/plans/plan_post_embedding_with_summary_for_reply.py`
- `grox/plans/plan_post_safety.py`
- `grox/plans/plan_reply_ranking.py`
- `grox/plans/plan_safety_ptos.py`
- `grox/plans/plan_spam_comment.py`
- `grox/summarizer/eapi_summarizer.py`
- `grox/summarizer/post_embedding_summarizer.py`
- `grox/summarizer/summarizer.py`
- `grox/tasks/task_banger_screen.py`
- `grox/tasks/task_embedding_pub.py`
- `grox/tasks/task_filters.py`
- `grox/tasks/task_grok_upa_action_with_labels.py`
- `grox/tasks/task_load_post_with_summary.py`
- `grox/tasks/task_load_user_recent_posts.py`
- `grox/tasks/task_media.py`
- `grox/tasks/task_multimodal_post_embedding.py`
- `grox/tasks/task_post_safety_screen_deluxe.py`
- `grox/tasks/task_pub.py`
- `grox/tasks/task_rank_replies.py`
- `grox/tasks/task_spam_detection.py`
- `phoenix/README.md`
- `phoenix/grok.py`
- `phoenix/recsys_model.py`
- `phoenix/recsys_retrieval_model.py`
- `phoenix/run_pipeline.py`
- `phoenix/run_ranker.py`
- `phoenix/run_retrieval.py`
- `phoenix/runners.py`
- `phoenix/test_recsys_model.py`
- `phoenix/test_recsys_retrieval_model.py`
- `thunder/posts/post_store.rs`
- `thunder/thunder_service.rs`
- `thunder/kafka/tweet_events_listener.rs`
- `thunder/kafka/tweet_events_listener_v2.rs`
