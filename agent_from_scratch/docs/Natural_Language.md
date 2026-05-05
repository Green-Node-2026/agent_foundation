Natural Language Processing (CO3086)
NLP 242 - Lab 6: Linear - Losgistic Regression
HO CHI MINH UNIVERSITY OF TECHNOLOGY
Vietnam National University Ho Chi Minh

# Problem 1

We are dealing with samples $x$ where $x$ is a single value. We would like to test two alternative regression models:

1. $y = ax + e$
2. $y = ax + bx^2 + e$

We make the same assumptions we had in class about the distribution of $e$ ($e \sim N(0, s^2)$).

a) Assume we have $n$ samples: $x_{1},\ldots ,x_{n}$ with their corresponding $y$ values: $y_{1},\ldots ,y_{n}$. Derive the value assigned to $b$ in model 2. You can use $a$ in the equation for $b$.

b) Which of the two models is more likely to fit the training data better and Explain?

(a) model 1
(b) model 2
(c) both will fit equally well
(d) impossible to tell

c) Which of the two models is more likely to fit the test data better and Explain?

(a) model 1
(b) model 2
(c) both will fit equally well
(d) impossible to tell

# Problem 2

a) Now assume we only observe a single input for each output (that is, a set of $\{x,y\}$ pairs). We would like to compare the following two models on our input dataset (for each one we split into training and testing sets to evaluate the learned model). Assume we have an unlimited amount of data:

A: $y = w^{2}x$
B: $y = wx$

Which of the following is correct and Explain:

1. There are datasets for which A would perform better than B.
2. There are datasets for which B would perform better than A.
3. Both 1 and 2 are correct.
4. They would perform equally well on all datasets.
2. For the data above we are now comparing the following two models:

1. $y=w_{1}^{2}x+w_{2}x$
2. $y=wx$

Note that model A now uses two parameters (though both multiply the same input value, $x$). Again, we assume unlimited data. Which of the following is correct (choose the answer that best describes the outcome) and Explain:

1. There are datasets for which A would perform better than B.
2. There are datasets for which B would perform better than A.
3. Both 1 and 2 are correct.
4. They would perform equally well on all datasets.

###### Problem 3

We are given a set of two-dimensional inputs and their corresponding output pair: $\{x_{i,1},x_{i,2},y_{i}\}$. We would like to use the following regression model to predict $y$:

$y_{i}=w_{1}^{2}x_{i,1}+w_{2}^{2}x_{i,2}$

Derive the optimal value for $w_{1}$ when using least squares as the target minimization function ($w_{2}$ may appear in your resulting equation). Note that there may be more than one possible value for $w_{1}$.

###### Problem 4

You are asked to use regularized linear regression to predict the target $Y\in\mathbb{R}$ from the eight-dimensional feature vector $X\in\mathbb{R}^{8}$. You define the model $Y=w^{T}X$ and then you recall from class the following three objective functions:

$\min_{w}\sum_{i=1}^{n}\left(y_{i}-w^{T}x_{i}\right)^{2}$ (4.1)
$\min_{w}\sum_{i=1}^{n}\left(y_{i}-w^{T}x_{i}\right)^{2}+\lambda\sum_{j=1}^{8}w_{j}^{2}$ (4.2)
$\min_{w}\sum_{i=1}^{n}\left(y_{i}-w^{T}x_{i}\right)^{2}+\lambda\sum_{j=1}^{8}|w_{j}|$ (4.3)
2. Show regularization terms in the objective functions above.

b) For large values of  $\lambda$  in objective 4.2 the bias would increase, decrease or remain unaffected?
c) For large values of  $\lambda$  in objective 4.3 the variance would increase, decrease or remain unaffected?
d) The following table contains the weights learned for all three objective functions (not in any particular order):

|   | Column A | Column B | Column C  |
| --- | --- | --- | --- |
|  w1 | 0.60 | 0.38 | 0.50  |
|  w2 | 0.30 | 0.23 | 0.20  |
|  w3 | -0.10 | -0.02 | 0.00  |
|  w4 | 0.20 | 0.15 | 0.09  |
|  w5 | 0.30 | 0.21 | 0.00  |
|  w6 | 0.20 | 0.03 | 0.00  |
|  w7 | 0.02 | 0.04 | 0.00  |
|  w8 | 0.26 | 0.12 | 0.05  |

# Problem 5

Suppose you are given the following classification task: predict the target  $Y \in \{0,1\}$  given two real valued features  $X_{1} \in \mathbb{R}$  and  $X_{2} \in \mathbb{R}$ . After some training, you learn the following decision rule:

Predict  $Y = 1$  iff  $w_{1}X_{1} + w_{2}X_{2} + w_{0} \geq 0$  and  $Y = 0$  otherwise

where  $w_{1} = 3$ ,  $w_{2} = 5$ , and  $w_{0} = -15$ .

a) Plot the decision boundary and label the region where we would predict  $Y = 1$  and  $Y = 0$ .
b) Suppose that we learned the above weights using logistic regression. Using this model, what would be our prediction for  $P(Y = 1 \mid X_1, X_2)$ ? (You may want to use the sigmoid function  $\sigma(x) = \frac{1}{1 + \exp(-x)}$ .)

$P(Y = 1\mid X_1,X_2) =$

# Problem 6

Consider a simple one-dimensional logistic regression model

$P(y = 1\mid x,\mathbf{w}) = g(w_0 + w_1x)$

where  $g(z) = \frac{1}{1 + \exp(z)}$  is the logistic function. The following figure shows two possible conditional distributions  $P(y = 1 \mid x; \mathbf{w})$ , viewed as a function of  $x$ , that we can get by changing the parameters  $\mathbf{w}$ .

![img-0.jpeg](data:image/jpeg;base64,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)

a) Please indicate the number of classification errors for each conditional given the labeled examples in the same figure.
b) One of the two classifiers corresponds to the maximum likelihood setting of the parameters  $w$  based on the labeled data in the figure, i.e., its parameters maximize the joint probability:

$$
P (y = 0 \mid x = - 1; w) \quad P (y = 1 \mid x = 0; w) \quad P (y = 0 \mid x = 1; w)
$$

Circle which one is the ML solution and briefly explain: Classifier 1 or Classifier 2

c) Would adding a regularization penalty  $|w_1|^2 / 2$  to the log-likelihood estimation criterion affect your choice of solution (Y/N)? (Note that the penalty above only regularizes  $w_1$ , not  $w_0$ .) Briefly explain why.

# Problem 7

In many real-world scenarios, our data has millions of dimensions, but a given example has only hundreds of non-zero features. For example, in document analysis with word counts for features, our dictionary may have millions of words, but a given document has only hundreds of unique words. In this question, we will make  $l_{2}$  regularized SGD efficient when our input data is sparse. Recall that in  $l_{2}$  regularized logistic regression, we want to maximize the following objective (in this problem we have excluded  $w_{0}$  for simplicity):

$$
F (\mathbf {w}) = \frac {1}{N} \sum_ {j = 1} ^ {N} l (x ^ {(j)}, y ^ {(j)}, \mathbf {w}) - \frac {\lambda}{2} \sum_ {i = 1} ^ {d} w _ {i} ^ {2}
$$

where  $l(x^{(j)},y^{(j)},\mathbf{w})$  is the logistic objective function

$$
l (x ^ {(j)}, y ^ {(j)}, \mathbf {w}) = y ^ {(j)} \left(\sum_ {i = 1} ^ {d} w _ {i} x _ {i} ^ {(j)}\right) - \ln \left(1 + \exp \left(\sum_ {i = 1} ^ {d} w _ {i} x _ {i} ^ {(j)}\right)\right)
$$

and the remaining sum is our regularization penalty.mWhen we do stochastic gradient descent

on point $(x^{(j)},y^{(j)})$, we are approximating the objective function as

$F(\mathbf{w})\approx l(x^{(j)},y^{(j)},\mathbf{w})-\frac{\lambda}{2}\sum_{i=1}^{d}w_{i}^{2}$

Definition of sparsity: Assume that our input data has $d$ features, i.e., $\mathbf{x}^{(j)}\in\mathbb{R}^{d}$. In this problem, we will consider the scenario where $x^{(j)}$ is sparse. Formally, let $s$ be the average number of nonzero elements in each example. We say that the data is sparse when $s\ll d$. In the following questions, your answer should take the sparsity of $x^{(j)}$ into consideration when possible.

Note: When we use a sparse data structure, we can iterate over the non-zero elements in $O(s)$ time, whereas a dense data structure requires $O(d)$ time.

1. Let us first consider the case when $\lambda=0$. Write down the SGD update rule for $\mathbf{w}$, where $\lambda=0$, using step size $\eta$, when the example $(x^{(j)},y^{(j)})$ is given.
2. If we use a dense data structure, what is the average time complexity to update $\mathbf{w}_{i}$ when $\lambda=0$? What if we use a sparse data structure? Justify your answer in one or two sentences.
3. Now let us consider the general case when $\lambda>0$. Write down the SGD update rule for $\mathbf{w}_{i}$ when $\lambda>0$, using step size $\eta$, given the example $(x^{(j)},y^{(j)})$.
4. If we use a dense data structure, what is the average time complexity to update $\mathbf{w}_{i}$ when $\lambda>0$?
5. Let $\mathbf{w}_{i}^{(t)}$ be the weight vector after $t$-th update. Now imagine that we perform $k$ SGD updates on $\mathbf{w}$ using examples $(x^{(t+1)},y^{(t+1)}),\ldots,(x^{(t+k)},y^{(t+k)})$, where $x^{(j)}_{i}=0$ for every example in the sequence. (i.e. the $i$-th feature is zero for all of the examples in the sequence). Express the new weight, $\mathbf{w}_{i}^{(t+k)}$, in terms of $\mathbf{w}_{i}^{(t)}$, $k$, $\eta$, and $\lambda$.
6. Using your answer in the previous part, come up with an efficient algorithm for regularized SGD when we use a sparse data structure. What is the average time complexity per example? (Hint: when do you need to update $w_{i}$?)

Algorithm 1: Sparse SGD Algorithm for Logistic Regression with Regularization
1: Initialize $c_{i}\gets 0$ for $i\in \{1,2,\ldots ,d\}$
2: for $j\in \{1,2,\dots ,n\}$ do
3: $\hat{p}\leftarrow \frac{1}{1 + \exp\left(-\sum_{k}w_{k}x_{k}^{(j)}\right)}$
4: for $i$ such that $x_{i}^{(j)}\neq 0$ do
5: $k\gets j - c_{i}$ {auxiliary variable $c_{i}$ holds the index of last time we see $x_{i}^{(j)}\neq 0$}
6: $w_{i}\gets w_{i}(1 - \eta \lambda)^{k}$ {apply all the regularization updates}
7: $w_{i}\gets w_{i} + \eta x_{i}^{(j)}(y^{(j)} - \hat{p})$ {regularization is done in previous step}
8: $c_{i}\gets j$ {remember last time we see $x_{i}^{(j)}\neq 0$}
9: end for
10: end for