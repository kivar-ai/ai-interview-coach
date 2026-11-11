# Demo answers

Paste whichever answer matches the question on screen. Good answers score 8 to 10.
For a more realistic demo, paste the WEAK answers at the bottom for 3 or 4 questions, so the report shows real gaps.

## q_python_001
**What is the difference between a list and a tuple in Python?**

Both lists and tuples are ordered sequences. A list is mutable, so you can add, remove or change items, while a tuple is immutable and cannot change after it is created. Tuples can be used as dictionary keys when their items are hashable, and they suit fixed data such as coordinates.

## q_python_002
**What is a dictionary in Python, and how do you look up a key that might not exist?**

A dictionary stores key-value pairs and looks up a value by its key. Keys must be hashable, such as strings, numbers or tuples. Looking up a missing key with square brackets raises a KeyError, so I use get(), which returns None or a default value I choose.

## q_python_003
**What is a list comprehension, and when would you use one?**

A list comprehension builds a new list from an iterable in a single expression, for example [x*x for x in numbers if x > 0]. It can include a condition to filter items, and it is shorter and usually faster than a loop with append. When the logic gets long or nested I switch to a normal loop for readability.

## q_python_004
**What is the mutable default argument trap in Python, as in def f(x, items=[])?**

Default argument values are evaluated once, when the function is defined, not on every call. If the default is a mutable object like a list, every call that leaves out the argument shares the same list, so changes made in one call show up in later calls. The fix is to use None as the default and create a new list inside the function when the argument is None.

## q_python_005
**What is the difference between == and is in Python?**

== checks whether two objects have the same value, while is checks whether two variables point to the exact same object in memory. For example, a = [1, 2] and b = [1, 2] are equal with == but a is b is False, because they are two different list objects. You should use is when comparing with None, like if x is None.

## q_python_006
**What is the difference between shallow copy and deep copy in Python?**

A shallow copy creates a new outer object, but the nested objects inside it are still shared with the original, so changing a nested list affects both. A deep copy recursively copies the nested objects as well, so the two are fully independent. In Python you use copy.copy() for a shallow copy and copy.deepcopy() for a deep copy.

## q_python_007
**What are Python generators, and how do yield and next() work?**

A generator produces values lazily, one at a time, instead of building the whole list in memory. A function with yield pauses at that line and hands back a value. Calling next() resumes it from where it stopped to produce the next value. This is useful for reading a very large file line by line.

## q_sql_001
**What is the difference between INNER JOIN and LEFT JOIN?**

INNER JOIN returns only the rows that have a match in both tables. LEFT JOIN returns every row from the left table plus the matching rows from the right table, and where there is no match the right-side columns are NULL. For example, LEFT JOIN customers to orders still lists customers who have no orders.

## q_sql_002
**What is the difference between WHERE and HAVING?**

WHERE filters individual rows before any grouping happens, while HAVING filters the groups after GROUP BY. That is why HAVING can use aggregate functions like COUNT or SUM and WHERE cannot. For example, SELECT dept, COUNT(*) FROM employees GROUP BY dept HAVING COUNT(*) > 5 returns only departments with more than five employees.

## q_sql_003
**What does a window function such as ROW_NUMBER() do, and how is it different from GROUP BY?**

A window function calculates a value for each row using a set of related rows, called the window, which is defined with OVER, PARTITION BY and ORDER BY. It keeps every row, unlike GROUP BY, which reduces many rows to one row per group. ROW_NUMBER() gives each row a sequence number within its partition, which is useful for the top 3 products per category.

## q_sql_004
**What is the difference between UNION and UNION ALL?**

UNION combines the results of two SELECT queries and removes duplicate rows, but UNION ALL keeps all the rows including duplicates. Because UNION ALL does not have to check for duplicates, it is usually faster. Both require the queries to return the same number of columns with compatible data types.

## q_sql_005
**What is a database index, and when does it help improve query performance?**

An index is a data structure that lets the database find rows quickly without scanning the whole table. It helps most on columns that are often used in WHERE conditions, JOINs or ORDER BY. The downside is that it needs extra storage, and it can slow down INSERT, UPDATE and DELETE because the index has to be updated too.

## q_sql_006
**What is the difference between a subquery and a Common Table Expression (CTE), and when would you use each?**

A subquery is a query nested inside another query. A CTE is defined with the WITH clause and is a named temporary result set that the main query can use. CTEs make multi-step queries easier to read and organize, and recursive CTEs can handle hierarchical data. I use subqueries for simple one-off cases and CTEs when a query has several logical steps or needs recursion.

## q_statistics_001
**What is a p-value?**

A p-value is the probability of seeing data at least as extreme as ours if the null hypothesis is true. A small p-value is evidence against the null hypothesis. The usual 0.05 cutoff is just a convention. And it is not the probability that the null hypothesis is true.

## q_statistics_002
**Explain the Central Limit Theorem.**

The Central Limit Theorem says that the distribution of sample means becomes approximately normal as the sample size grows, whatever the shape of the population, as long as it has finite variance and the sample is large enough. The sample means centre on the population mean, and their spread, the standard error, shrinks as n grows. It matters because many tests and confidence intervals assume normality.

## q_statistics_003
**What is the difference between population and sample?**

A population is the complete group we want to study, and a sample is a smaller subset taken from it to represent it. We use samples because collecting data from a whole population is expensive and time-consuming. A good sample should represent the population fairly.

## q_statistics_004
**What is the difference between mean, median, and mode?**

The mean is the sum of all values divided by the number of observations, the median is the middle value in sorted data, and the mode is the most frequently occurring value. The median is less affected by extreme outliers, so it is often better than the mean for skewed data.

## q_statistics_005
**What is the difference between correlation and causation?**

Correlation measures the strength and direction of the relationship between two variables, while causation means a change in one variable directly produces a change in the other. Correlation does not prove causation, because a confounding variable can explain it. For example, ice cream sales and drowning both rise in summer because of hot weather, not because one causes the other.

## q_statistics_006
**What is the difference between Type I and Type II errors in hypothesis testing?**

A Type I error is rejecting a null hypothesis that is actually true, a false positive. Its probability is alpha, the significance level. A Type II error is failing to reject a null hypothesis that is actually false, a false negative, and its probability is beta. Statistical power is 1 minus beta.

## q_machine_learning_001
**What is overfitting and how can you reduce it?**

Overfitting is when a model learns the training data including its noise, so it does well on training data but poorly on unseen data. You can spot it by comparing training performance with validation performance. To reduce it you can use more data, regularization, cross-validation, early stopping, or a simpler model.

## q_machine_learning_002
**Explain the bias-variance trade-off.**

Bias is error from overly simple assumptions, which leads to underfitting. Variance is error from being too sensitive to the training data, which leads to overfitting. Making a model more complex lowers bias but raises variance, so the goal is a balance that minimizes error on unseen data. For example, a straight line fitted to curved data has high bias, while a very deep decision tree has high variance.

## q_machine_learning_003
**What is the difference between precision and recall, and when would you prefer each?**

Precision is TP divided by TP plus FP: of everything predicted positive, how much was really positive. Recall is TP divided by TP plus FN: of all the actual positives, how many the model found. Prefer precision when false positives are costly, like spam filtering where a real email must not be lost. Prefer recall when missing a positive is costly, like disease screening or fraud detection.

## q_machine_learning_004
**What is the difference between training, validation, and test datasets?**

The training set is used to fit the model, the validation set is used to tune hyperparameters and choose between models, and the test set is used once at the end to measure performance on unseen data. They are kept separate to avoid data leakage and an overly optimistic estimate.

## q_machine_learning_005
**What is the difference between L1 and L2 regularization in machine learning?**

L1 regularization adds the absolute values of the coefficients as a penalty and can push some coefficients to exactly zero, which helps with feature selection. L2 regularization adds the squared coefficient values as a penalty and shrinks coefficients but generally does not make them exactly zero. Both help control model complexity and reduce overfitting.

## q_machine_learning_006
**What is k-fold cross-validation, and how does it help evaluate a machine learning model?**

K-fold cross-validation splits the dataset into K roughly equal folds. The model is trained K times, each time validating on a different fold and training on the other K minus 1 folds. The scores from the K runs are averaged. This gives a more reliable estimate than a single split, especially when data is limited. Preprocessing such as scaling should be fitted inside each training fold to prevent data leakage.

## q_llm_genai_001
**What is RAG and why is it used?**

RAG first retrieves relevant passages from an external knowledge source such as a vector database, then gives them to the language model to write the answer. It reduces hallucination, lets the model cite sources, and adds new or private knowledge without retraining the model.

## Weak answers (use these for 3 or 4 questions)

1. I am not very familiar with this topic, I think it is something related to how the data is stored.

2. They are almost the same thing, one is just a bit faster than the other.

3. I have heard about this but I do not remember the details.

4. It is used to make the model better, I think you just run it on more data.
