# coding=utf-8
# Copyright 2020 The Google Research Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Training and evaluation"""

import run_lib
from absl import app
from absl import flags
from ml_collections.config_flags import config_flags
import tensorflow as tf
import logging
import os
# import chex

FLAGS = flags.FLAGS

config_flags.DEFINE_config_file(
  "config", None, "Training configuration.", lock_config=True)
flags.DEFINE_string("workdir", None, "Work directory.")
flags.DEFINE_enum("mode", None, ["train", "eval", "train_deq"], "Running mode: train or eval")
flags.DEFINE_string("eval_folder", "eval_test_bpd",
                    "The folder name for storing evaluation results")
flags.DEFINE_string("deq_folder", "flowpp_dequantizer", "The folder name for dequantizer training.")
flags.mark_flags_as_required(["workdir", "config", "mode"])


def main(argv):
  tf.config.experimental.set_visible_devices([], "GPU")
  os.environ['XLA_PYTHON_CLIENT_PREALLOCATE'] = 'false'

  if FLAGS.mode == "train":
    # Create the working directory
    tf.io.gfile.makedirs(FLAGS.workdir)
    # Set logger so that it outputs to both console and file
    # Make logging work for both disk and Google Cloud Storage
    gfile_stream = tf.io.gfile.GFile(os.path.join(FLAGS.workdir, 'stdout.txt'), 'w')
    handler = logging.StreamHandler(gfile_stream)
    formatter = logging.Formatter('%(levelname)s - %(filename)s - %(asctime)s - %(message)s')
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel('INFO')
    # Run the training pipeline
    if FLAGS.mode == "train":
      run_lib.train(FLAGS.config, FLAGS.workdir)
    else:
      run_lib.deq_score_joint_train(FLAGS.config, FLAGS.workdir)
  elif FLAGS.mode == "eval":
    # Run the evaluation pipeline
    run_lib.evaluate(FLAGS.config, FLAGS.workdir, FLAGS.eval_folder, FLAGS.deq_folder)
  elif FLAGS.mode == "train_deq":
    assert tf.io.gfile.exists(FLAGS.workdir)
    new_workdir = os.path.join(FLAGS.workdir, FLAGS.deq_folder)
    tf.io.gfile.makedirs(new_workdir)
    gfile_stream = tf.io.gfile.GFile(os.path.join(new_workdir, 'stdout.txt'), 'w')
    handler = logging.StreamHandler(gfile_stream)
    formatter = logging.Formatter('%(levelname)s - %(filename)s - %(asctime)s - %(message)s')
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel('INFO')
    # with chex.fake_pmap():
    run_lib.train_deq(FLAGS.config, FLAGS.workdir, new_workdir)
  else:
    raise ValueError(f"Mode {FLAGS.mode} not recognized.")


if __name__ == "__main__":
  app.run(main)
