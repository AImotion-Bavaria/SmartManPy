# ===========================================================================
# Copyright 2013 University of Limerick
#
# This file is part of DREAM.
#
# DREAM is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DREAM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with DREAM.  If not, see <http://www.gnu.org/licenses/>.
# ===========================================================================
"""
Created on 14 Feb 2013

@author: George
"""

"""
holds methods for generations of numbers from different distributions
"""

import math
import numpy.random as rnd

class RandomNumberGenerator(object):
    # data should be given as a dict:
    #     "distribution": {
    #         "distributionType": {
    #             "mean": "2*x + 10",
    #             "stdev": "1",
    #             "parameterX":"X",
    #            ...
    #         },
    def __init__(self, obj, distribution):
        # if the distribution is not given as a dictionary throw error
        if not isinstance(distribution, dict):
            raise ValueError("distribution must be given as a dict")
        # check in case an unknown distribution was given
        unknownDistribution = True
        for key in list(distribution.keys()):
            if key in [
                "Fixed",
                "Normal",
                "Exp",
                "Gamma",
                "Logistic",
                "Erlang",
                "Geometric",
                "Lognormal",
                "Weibull",
                "Cauchy",
                "Triangular",
            ]:
                unknownDistribution = False
                break
        if unknownDistribution:
            # XXX accept old format ??
            if "distributionType" in distribution:
                from copy import copy

                distribution = copy(distribution)  # we do not store this in json !
                distribution[distribution.pop("distributionType")] = distribution
            else:
                raise ValueError(
                    "Unknown distribution %r used in %s %s"
                    % (distribution, obj.__class__, obj.id)
                )
        # pop irrelevant keys
        for key in list(distribution.keys()):
            if key not in [
                "Fixed",
                "Normal",
                "Exp",
                "Gamma",
                "Logistic",
                "Erlang",
                "Geometric",
                "Lognormal",
                "Weibull",
                "Cauchy",
                "Triangular",
            ]:
                distribution.pop(key, None)
        self.distribution = distribution
        self.distributionType = list(distribution.keys())[0]
        parameters = distribution[self.distributionType]
        # if a parameter is passed as None or empty string set it to 0
        for key in parameters:
            if parameters[key] in [None, ""]:
                parameters[key] = 0.0
        self.mean = str(parameters.get("mean", 0))
        self.stdev = str(parameters.get("stdev", 0))
        self.min = str(parameters.get("min", None))
        self.max = str(parameters.get("max", None))
        self.alpha = str(parameters.get("alpha", 0))
        self.beta = str(parameters.get("beta", 0))
        self.probability = str(parameters.get("probability", 0))
        self.shape = str(parameters.get("shape", 0))
        self.scale = str(parameters.get("scale", 0))
        self.location = str(parameters.get("location", 0))
        self.rate = str(parameters.get("rate", 0))
        self.obj = obj


    def generateNumber(self, start_time=0):
        from .Globals import G
        x = G.env.now - start_time
        if x < 0:
            return None

        if eval(self.probability) != 0:
            if rnd.binomial(1, eval(self.probability)) == 0:
                return 0
        if self.distributionType == "Fixed":  # if the distribution is Fixed
            return eval(self.mean)
        elif self.distributionType == "Exp":  # if the distribution is Exponential
            return rnd.exponential(eval(self.mean))
        elif self.distributionType == "Normal":  # if the distribution is Normal
            if (self.max != "None" and self.min != "None"):
                if eval(self.max) < eval(self.min):
                    raise ValueError(
                        "Normal distribution for %s uses wrong "
                        "parameters. max (%s) > min (%s)"
                        % (self.obj.id, eval(self.max), eval(self.min))
                    )
            while 1:
                number = rnd.normal(eval(self.mean), eval(self.stdev))
                if self.max == "None" and self.min != "None":
                    if number < eval(self.min):
                        continue
                    else:
                        return number
                elif self.max != "None" and self.min == "None":
                    if number > eval(self.max):
                        continue
                    else:
                        return number
                elif self.max == "None" and self.min == "None":
                    return number
                else:
                    if (number > eval(self.max) or number < eval(self.min)):
                        # if the number is out of bounds repeat the process
                        ##if max=0 this means that we did not have time "time" bounds
                        continue
                    else:  # if the number is in the limits stop the process
                        return number
        elif (self.distributionType == "Gamma" or self.distributionType == "Erlang"):
            # if the distribution is gamma or erlang
            # in case shape is given instead of alpha
            if not self.alpha:
                self.alpha = self.shape
            # in case rate is given instead of beta
            if not self.beta:
                self.beta = 1 / float(eval(self.rate))
            return rnd.gamma(eval(self.alpha), eval(self.beta))
        elif self.distributionType == "Logistic":  # if the distribution is Logistic
            return rnd.logistic(eval(self.location), eval(self.scale))
        elif self.distributionType == "Geometric":  # if the distribution is Geometric
            return rnd.geometric(eval(self.mean))
        elif self.distributionType == "Lognormal":  # if the distribution is Lognormal
            return rnd.lognormal(eval(self.mean), eval(self.stdev))
        elif self.distributionType == "Weibull":  # if the distribution is Weibull
            return rnd.weibull(eval(self.shape))
        elif self.distributionType == "Cauchy":  # if the distribution is Cauchy
            # XXX from http://www.johndcook.com/python_cauchy_rng.html
            while 1:
                number = eval(self.location) + eval(self.scale) * math.tan(math.pi * (rnd.random_sample() - 0.5))
                if number > 0:
                    return number
                else:
                    continue
        elif self.distributionType == "Triangular":  # if the distribution is Triangular
            return rnd.triangular(left=eval(self.min), mode=eval(self.mean), right=eval(self.max))
        else:
            raise ValueError(
                "Unknown distribution %r used in %s %s"
                % (self.distributionType, self.obj.__class__, self.obj.id)
            )
