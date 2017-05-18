#-*- coding: utf-8 -*-
'''
Created on 2017-05-18

@author: Frankchen0130
'''
import sys, random, math
from operator import itemgetter


random.seed(0)


class ItemBasedCF():
    ''' TopN recommendation - ItemBasedCF '''
    def __init__(self):
        self.trainset = {}
        self.testset = {}

        self.n_sim_movie = 20
        self.n_rec_movie = 10

        self.movie_sim_mat = {}
        self.movie_popular = {}
        self.movie_count = 0

        print('Similar movie number = %d' % self.n_sim_movie)
        print('Recommended movie number = %d' % self.n_rec_movie)


    @staticmethod
    def loadfile(filename):
        ''' load a file, return a generator. '''
        fp = open(filename, 'r')
        for i, line in enumerate(fp):
            yield line.strip('\r\n')
            if i % 100000 == 0:
                print('loading %s(%s)' % (filename, i))
        fp.close()
        print('load %s succ' % filename)


    def generate_dataset(self, filename, pivot=0.7):
        ''' load rating data and split it to training set and test set '''
        trainset_len = 0
        testset_len = 0

        for line in self.loadfile(filename):
            user, movie, rating, _ = line.split('::')
            # split the data by pivot
            if (random.random() < pivot):
                self.trainset.setdefault(user, {})
                self.trainset[user][movie] = int(rating)
                trainset_len += 1
            else:
                self.testset.setdefault(user, {})
                self.testset[user][movie] = int(rating)
                testset_len += 1

        print('split training set and test set succ')
        print('train set = %s' % trainset_len)
        print('test set = %s' % testset_len)


    def calc_movie_sim(self):
        ''' calculate movie similarity matrix '''
        print('counting movies number and popularity...')

        for user, movies in self.trainset.items():
            for movie in movies:
                # count item popularity 
                if movie not in self.movie_popular:
                    self.movie_popular[movie] = 0
                self.movie_popular[movie] += 1

        print('count movies number and popularity succ')

        # save the total number of movies
        self.movie_count = len(self.movie_popular)
        print('total movie number = %d' % self.movie_count)

        # count co-rated users between items
        itemsim_mat = self.movie_sim_mat
        print('building co-rated users matrix...')

        for user, movies in self.trainset.items():
            for m1 in movies:
                for m2 in movies:
                    if m1 == m2: continue
                    itemsim_mat.setdefault(m1,{})
                    itemsim_mat[m1].setdefault(m2,0)
                    itemsim_mat[m1][m2] += 1

        print('build co-rated users matrix succ')

        # calculate similarity matrix 
        print('calculating movie similarity matrix...')
        simfactor_count = 0
        PRINT_STEP = 2000000

        for m1, related_movies in itemsim_mat.items():
            for m2, count in related_movies.items():
                itemsim_mat[m1][m2] = count / math.sqrt(
                        self.movie_popular[m1] * self.movie_popular[m2])
                simfactor_count += 1
                if simfactor_count % PRINT_STEP == 0:
                    print('calculating movie similarity factor(%d)' % simfactor_count)

        print('calculate movie similarity matrix(similarity factor) succ')
        print('Total similarity factor number = %d' %simfactor_count)


    def recommend(self, user):
        ''' Find K similar movies and recommend N movies. '''
        K = self.n_sim_movie
        N = self.n_rec_movie
        rank = {}
        watched_movies = self.trainset[user]

        for movie, rating_score in watched_movies.items():
            for related_movie, simi_score in sorted(self.movie_sim_mat[movie].items(),
                    key=itemgetter(1), reverse=True)[:K]:
                if related_movie in watched_movies:
                    continue
                rank.setdefault(related_movie, 0)
                rank[related_movie] += rating_score * simi_score
        # return the N best movies
        return sorted(rank.items(), key=itemgetter(1), reverse=True)[:N]


    def evaluate(self):
        ''' return precision, recall, coverage and popularity '''
        print('Evaluation start...')

        N = self.n_rec_movie
        #  varables for precision and recall 
        hit = 0
        rec_count = 0
        test_count = 0
        # varables for coverage
        all_rec_movies = set()
        # varables for popularity
        popular_sum = 0

        for i, user in enumerate(self.trainset):
            if i % 500 == 0:
                print('recommended for %d users' % i)
            test_movies = self.testset.get(user, {})
            rec_movies = self.recommend(user)
            for movie, w in rec_movies:
                if movie in test_movies:
                    hit += 1
                all_rec_movies.add(movie)
                popular_sum += math.log(1 + self.movie_popular[movie])
            rec_count += N
            test_count += len(test_movies)

        precision = hit / (1.0 * rec_count)
        recall = hit / (1.0 * test_count)
        coverage = len(all_rec_movies) / (1.0 * self.movie_count)
        popularity = popular_sum / (1.0 * rec_count)

        print('precision=%.4f\trecall=%.4f\tcoverage=%.4f\tpopularity=%.4f' \
                % (precision, recall, coverage, popularity))


if __name__ == '__main__':
    ratingfile = 'ml-1m/ratings.dat'
    itemcf = ItemBasedCF()
    itemcf.generate_dataset(ratingfile)
    itemcf.calc_movie_sim()
    itemcf.evaluate()
