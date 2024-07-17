def exponential_cdf(x):
    """
    Calculates the exponential cdf.

    :param x: The value.
    :return: The exponential cdf.
    """
    return 1 - 2 ** -x

def log_normal_cdf(x):
    """
    Calculates the log normal cdf.

    :param x: The value.
    :return: The log normal cdf.
    """
    # approximation
    return x / (1 + x)

def calculate_rank(all_commits, commits, prs, issues, reviews, repos, stars, followers):
    """
    Calculates the user's rank.

    :param all_commits: Whether `include_all_commits` was used.
    :param commits: Number of commits.
    :param prs: The number of pull requests.
    :param issues: The number of issues.
    :param reviews: The number of reviews.
    :param repos: Total number of repos.
    :param stars: The number of stars.
    :param followers: The number of followers.
    :return: The user's rank as a dictionary with level and percentile.
    """
    COMMITS_MEDIAN = 1000 if all_commits else 250
    COMMITS_WEIGHT = 2
    PRS_MEDIAN = 50
    PRS_WEIGHT = 3
    ISSUES_MEDIAN = 25
    ISSUES_WEIGHT = 1
    REVIEWS_MEDIAN = 2
    REVIEWS_WEIGHT = 1
    STARS_MEDIAN = 50
    STARS_WEIGHT = 4
    FOLLOWERS_MEDIAN = 10
    FOLLOWERS_WEIGHT = 1

    TOTAL_WEIGHT = (COMMITS_WEIGHT + PRS_WEIGHT + ISSUES_WEIGHT +
                    REVIEWS_WEIGHT + STARS_WEIGHT + FOLLOWERS_WEIGHT)

    THRESHOLDS = [1, 12.5, 25, 37.5, 50, 62.5, 75, 87.5, 100]
    LEVELS = ["S", "A+", "A", "A-", "B+", "B", "B-", "C+", "C"]

    rank = (1 - (COMMITS_WEIGHT * exponential_cdf(commits / COMMITS_MEDIAN) +
                 PRS_WEIGHT * exponential_cdf(prs / PRS_MEDIAN) +
                 ISSUES_WEIGHT * exponential_cdf(issues / ISSUES_MEDIAN) +
                 REVIEWS_WEIGHT * exponential_cdf(reviews / REVIEWS_MEDIAN) +
                 STARS_WEIGHT * log_normal_cdf(stars / STARS_MEDIAN) +
                 FOLLOWERS_WEIGHT * log_normal_cdf(followers / FOLLOWERS_MEDIAN)) /
                TOTAL_WEIGHT)

    level = next(level for threshold, level in zip(THRESHOLDS, LEVELS) if rank * 100 <= threshold)

    return {"level": level, "percentile": rank * 100}