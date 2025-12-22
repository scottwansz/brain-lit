about_vector_type = """
Vector is type of field which has more than one value for every date and instrument. 
Vector data fields have to be converted into matrix data fields using vector operators before using with other operators and matrix data fields. 
"""

about_data_coverage = """
Coverage refers to the fraction of the total instruments present in the universe for which the given data field has a defined value. 
Low coverage fields can be handled by making use of backfill operators like ts_backfill, kth element, group_backfill, etc. 
"""

start_guide_sentiment = """
Getting started with Sentiment Datasets

Tips for getting started with Sentiment Datasets:
Sentiment represents the aggregate market mood about stocks.
Rising stock price is characterized by positive or "bullish" sentiment, while a declining stock price is characterized by negative or "bearish" sentiment.
The intensity of sentiment represents the strength of the sentiment.
A high intensity of sentiment, regardless of the mood or direction, exists when strong market moves occur.
For example, positive market sentiment combined with high intensity is typically a characteristic of strong bullish moves in prices.
Sentiment data can help us better predict market behavior and improve our forecasting, not only for price direction but also for volatility and volume traded.
Sentiment data have data fields of sentiment scores of an event. Unlike fundamental data, these data naturally have high frequencies, which leads to high turnovers in an Alpha.
To achieve reasonable margin rates, you are advised to use the following operations: hump_decay, ts_decay_linear, and ts_decay_exp_window. But you should be careful with the usage of lookback days greater than 63 (i.e., one quarter) as older events may have no impact.
Data may be based on information from newspapers, news websites, Facebook, Twitter, blog posts, discussion groups, and forums.
Social sentiment indicators help investors identify information in social media that could cause a stock's price to increase or decrease in the near future. They also help businesses understand how they may be performing in the eyes of their consumers.

Example Alpha Ideas:
Long/short stocks with positive/negative sentiment, filtering out days and stocks with low sentiment volume.
Use sentiment volume as a proxy for the market's attention towards a stock. This could be used directly as a stock returns predictor or a condition in trade_when.

Sentiment数据的相关Alpha表达式模板：
<time_series_operator/>(<positive_sentiment/> - <negative_sentiment/>, <days/>)
隐含假设：如果与之前相比，一家公司的净情绪是正面的，那么股价可能会上升。

具体实现: 
直接对净情绪值进行时间序列运算。 使用合理的天数参数，例如周（5天）、月（20天）、季（60天）或年（250天）。  
Sentiment Model and Neutralization to improve Alpha.
除了这个简单的实现，您可能想要将其扩展为更复杂的格式，例如:
positive_sentiment = rank(<backfill_op/>(<positive_sentiment_field/>, days));
negative_sentiment = rank(<backfill_op/>(<negative_sentiment_field/>, days));
sentiment_difference = <compare_op/>(positive_sentiment, negative_sentiment);
<time_series_operator/>(sentiment_difference, days)
通过在模板中更改数据字段、运算符和参数，您可以有效地生成多样化的可提交Alpha。

实现细节说明:
<backfill_op/>: 由于情绪数据通常覆盖度较低，因此使用ts_backfill或to_nan进行数据回填以实现更高的覆盖度是更好的选择。 
rank：此模板在回填情绪上使用Rank排名运算符，这确保了数据分布处于可控的范围内。这一步骤还从原始数据中去除了一些噪音。
<compare_op/>: 除了原始的减法运算符，您还可以从其他比较运算符中进行选择。 
"""

start_guide = {
    "sentiment": start_guide_sentiment,
}