Natural Language Processing (CO3086)
NLP 242 - Lab 6: Linear - Losgistic Regression
HO CHI MINH UNIVERSITY OF TECHNOLOGY
Vietnam National University Ho Chi Minh
Problem 1
We are dealing with samplesx wherex is a single value. We would like to test two alternative
regression models:
1. y =ax +e
2. y =ax +bx2 +e
We make the same assumptions we had in class about the distribution of e (e∼N(0,s 2)).
a) Assume we have n samples: x1,...,x n with their corresponding y values: y1,...,y n.
Derive the value assigned to b in model 2. You can use a in the equation for b.
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
Problem 2
a) Now assume we only observe a single input for each output (that is, a set of {x,y}
pairs). We would like to compare the following two models on our input dataset (for
each one we split into training and testing sets to evaluate the learned model). Assume
we have an unlimited amount of data:
A: y =w2x
B: y =wx
Which of the following is correct and Explain:
1

--- Page Break ---

(a) There are datasets for which A would perform better than B.
(b) There are datasets for which B would perform better than A.
(c) Both 1 and 2 are correct.
(d) They would perform equally well on all datasets.
b) For the data above we are now comparing the following two models:
A: y =w2
1x +w2x
B: y =wx
Note that model A now uses two parameters (though both multiply the same input
value,x). Again, we assume unlimited data. Which of the following is correct (choose
the answer that best describes the outcome) and Explain:
(a) There are datasets for which A would perform better than B.
(b) There are datasets for which B would perform better than A.
(c) Both 1 and 2 are correct.
(d) They would perform equally well on all datasets.
Problem 3
We are given a set of two-dimensional inputs and their corresponding output pair:
{xi,1,x i,2,y i}. We would like to use the following regression model to predict y:
yi =w2
1xi,1 +w2
2xi,2
Derive the optimal value forw1 when using least squares as the target minimization function
(w2 may appear in your resulting equation). Note that there may be more than one possible
value for w1.
Problem 4
You are asked to use regularized linear regression to predict the target Y∈R from the eight-
dimensional feature vector X∈R8. You define the model Y = wTX and then you recall
from class the following three objective functions:
minw
n∑
i=1
(
yi−wTxi
)2
(4.1)
minw
n∑
i=1
(
yi−wTxi
)2
+λ
8∑
j=1
w2
j (4.2)
minw
n∑
i=1
(
yi−wTxi
)2
+λ
8∑
j=1
|wj| (4.3)
a) Show regularization terms in the objective functions above.
2

--- Page Break ---

b) For large values of λin objective 4.2 the bias would increase, decrease or remain unaf-
fected?
c) For large values of λin objective 4.3 the variance would increase, decrease or remain
unaffected?
d) The following table contains the weights learned for all three objective functions (not
in any particular order):
Column A Column B Column C
w1 0.60 0.38 0.50
w2 0.30 0.23 0.20
w3 -0.10 -0.02 0.00
w4 0.20 0.15 0.09
w5 0.30 0.21 0.00
w6 0.20 0.03 0.00
w7 0.02 0.04 0.00
w8 0.26 0.12 0.05
Problem 5
Suppose you are given the following classification task: predict the target Y ∈{0, 1}given
two real valued features X1∈R and X2∈R. After some training, you learn the following
decision rule:
Predict Y = 1 iff w1X1 +w2X2 +w0≥0 and Y = 0 otherwise
where w1 = 3, w2 = 5, and w0 =−15.
a) Plot the decision boundary and label the region where we would predict Y = 1 and
Y = 0.
b) Suppose that we learned the above weights using logistic regression. Using this model,
what would be our prediction forP (Y = 1|X1,X 2)? (You may want to use the sigmoid
function σ(x) = 1
1+exp(−x).)
P (Y = 1|X1,X 2) =
Problem 6
Consider a simple one-dimensional logistic regression model
P (y = 1|x, w) =g(w0 +w1x)
whereg(z) = 1
1+exp(z) is the logistic function. The following figure shows two possible condi-
tional distributions P (y = 1|x; w), viewed as a function of x, that we can get by changing
the parameters w.
3

--- Page Break ---

−2 −1.5 −1 −0.5 0.5 1 1.5 2
0.2
0.4
0.6
0.8
1
y = 0 y = 0
y = 1
x
P (y = 1|x, ˆw)
(2) P (y = 1|x, ˆw)
(1) P (y = 1|x, ˆw)
a) Please indicate the number of classification errors for each conditional given the labeled
examples in the same figure.
b) One of the two classifiers corresponds to the maximum likelihood setting of the param-
eters w based on the labeled data in the figure, i.e., its parameters maximize the joint
probability:
P (y = 0|x =−1;w) P (y = 1|x = 0;w) P (y = 0|x = 1;w)
Circle which one is the ML solution and briefly explain: Classifier 1 or Classifier 2
c) Would adding a regularization penalty|w1|2/2 to the log-likelihood estimation criterion
affect your choice of solution (Y/N)? (Note that the penalty above only regularizes w1,
not w0.) Briefly explain why.
Problem 7
In many real-world scenarios, our data has millions of dimensions, but a given example has
only hundreds of non-zero features. For example, in document analysis with word counts for
features, our dictionary may have millions of words, but a given document has only hundreds
of unique words. In this question, we will make l2 regularized SGD efficient when our input
data is sparse. Recall that in l2 regularized logistic regression, we want to maximize the
following objective (in this problem we have excluded w0 for simplicity):
F(w) = 1
N
N∑
j=1
l(x(j),y (j), w)−λ
2
d∑
i=1
w2
i
where l(x(j),y (j), w) is the logistic objective function
l(x(j),y (j), w) =y(j)
( d∑
i=1
wix(j)
i
)
−ln
(
1 + exp
( d∑
i=1
wix(j)
i
))
and the remaining sum is our regularization penalty.mWhen we do stochastic gradient descent
4

--- Page Break ---

on point (x(j),y (j)), we are approximating the objective function as
F(w)≈l(x(j),y (j), w)−λ
2
d∑
i=1
w2
i
Definition of sparsity: Assume that our input data has d features, i.e., x(j)∈Rd. In
this problem, we will consider the scenario where x(j) is sparse. Formally, let s be the
average number of nonzero elements in each example. We say that the data is sparse when
s≪d. In the following questions, your answer should take the sparsity of x(j) into
consideration when possible.
Note: When we use a sparse data structure, we can iterate over the non-zero elements in
O(s) time, whereas a dense data structure requires O(d) time.
a) Let us first consider the case when λ= 0. Write down the SGD update rule for w,
where λ= 0, using step size η, when the example (x(j),y (j)) is given.
b) If we use a dense data structure, what is the average time complexity to update wi
when λ= 0? What if we use a sparse data structure? Justify your answer in one or
two sentences.
c) Now let us consider the general case when λ>0. Write down the SGD update rule for
wi when λ>0, using step size η, given the example (x(j),y (j)).
d) If we use a dense data structure, what is the average time complexity to update wi
when λ>0?
e) Let w(t)
i be the weight vector after t-th update. Now imagine that we perform k SGD
updates on w using examples ( x(t+1),y (t+1)),..., (x(t+k),y (t+k)), where x(j)
i = 0 for
every example in the sequence. (i.e. the i-th feature is zero for all of the examples in
the sequence). Express the new weight, w(t+k)
i , in terms of w(t)
i , k, η, and λ.
f) Using your answer in the previous part, come up with an efficient algorithm for regu-
larized SGD when we use a sparse data structure. What is the average time complexity
per example? (Hint: when do you need to update wi?)
5

--- Page Break ---

Algorithm 1: Sparse SGD Algorithm for Logistic Regression with Regularization
1: Initialize ci←0 for i∈{1, 2,...,d}
2: for j∈{1, 2,...,n}do
3: ˆp← 1
1+exp
(
−
∑
k wkx(j)
k
)
4: for i such that x(j)
i ̸= 0 do
5: k←j−ci{auxiliary variable ci holds the index of last time we see x(j)
i ̸= 0}
6: wi←wi(1−ηλ)k{apply all the regularization updates}
7: wi←wi +ηx(j)
i (y(j)−ˆp){regularization is done in previous step}
8: ci←j{remember last time we see x(j)
i ̸= 0}
9: end for
10: end for
6