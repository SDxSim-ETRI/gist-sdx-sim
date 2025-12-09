# 
# Copyright (C) 2021 NVIDIA Corporation.  All rights reserved.
# Licensed under the NVIDIA Source Code License.
# See LICENSE at https://github.com/nv-tlabs/ATISS.
# Authors: Despoina Paschalidou, Amlan Kar, Maria Shugrina, Karsten Kreis,
#          Andreas Geiger, Sanja Fidler
# 

import numpy as np
import pickle

import torch
from .utils import parse_threed_future_models


class ThreedFutureDataset(object):
    def __init__(self, objects):
        assert len(objects) > 0
        self.objects = objects

    def __len__(self):
        return len(self.objects)

    def __str__(self):
        return "Dataset contains {} objects with {} discrete types".format(
            len(self)
        )

    def __getitem__(self, idx):
        return self.objects[idx]

    def _filter_objects_by_label(self, label):
        if label is not None:
            return [oi for oi in self.objects if oi.label == label]
        else:  # return all objects if `label` is not specified
            return [oi for oi in self.objects]

    def get_closest_furniture_to_box(self, query_label, query_size):
        objects = self._filter_objects_by_label(query_label)

        mses = {}
        for i, oi in enumerate(objects):
            mses[oi] = np.sum((oi.size - query_size)**2, axis=-1)
        sorted_mses = [k for k, v in sorted(mses.items(), key=lambda x:x[1])]
        return sorted_mses[0]

    def get_closest_furniture_to_2dbox(self, query_label, query_size):
        objects = self._filter_objects_by_label(query_label)

        mses = {}
        for i, oi in enumerate(objects):
            mses[oi] = (
                (oi.size[0] - query_size[0])**2 +
                (oi.size[2] - query_size[1])**2
            )
        sorted_mses = [k for k, v in sorted(mses.items(), key=lambda x: x[1])]
        return sorted_mses[0]

    ################################ For InstructScene BEGIN ################################

    def get_closest_furniture_to_objfeat_and_size(self, query_label, query_size, query_objfeat, objfeat_type):
        # 1. Filter objects by label
        # 2. Sort objects by feature cosine similarity
        # 3. Pick top N objects (N=1 by default), i.e., select objects by feature cossim only
        # 4. Sort remaining objects by size MSE
        objects = self._filter_objects_by_label(query_label)

        cos_sims = {}
        # for i, oi in enumerate(objects):  #ailabktw : org
        #     query_objfeat = query_objfeat / np.linalg.norm(query_objfeat, axis=-1, keepdims=True)  # L2 normalize
        #     assert np.allclose(np.linalg.norm(eval(f"oi.{objfeat_type}_features"), axis=-1), 1.0)  # sanity check: already L2 normalized
        #     cos_sims[oi] = np.dot(eval(f"oi.{objfeat_type}_features"), query_objfeat)
        for i, oi in enumerate(objects):    #ailabktw
            try:
                query_objfeat = query_objfeat / np.linalg.norm(query_objfeat, axis=-1, keepdims=True)  # L2 normalize
                assert np.allclose(np.linalg.norm(eval(f"oi.{objfeat_type}_features"), axis=-1), 1.0)  # sanity check: already L2 normalized
                cos_sims[oi] = np.dot(eval(f"oi.{objfeat_type}_features"), query_objfeat)
            except:
                print(f"oi: {oi}, query_objfeat: {query_objfeat}")
                print(f"oi.{objfeat_type}_features: {eval(f'oi.{objfeat_type}_features')}")
                cos_sims[oi] = 0.0

        sorted_cos_sims = [k for k, v in sorted(cos_sims.items(), key=lambda x:x[1], reverse=True)]

        N = 1  # TODO: make it configurable
        filted_objects = sorted_cos_sims[:min(N, len(sorted_cos_sims))]
        mses = {}
        for i, oi in enumerate(filted_objects):
            mses[oi] = np.sum((oi.size - query_size)**2, axis=-1)
        sorted_mses = [k for k, v in sorted(mses.items(), key=lambda x:x[1])]
        return sorted_mses[0], cos_sims[sorted_mses[0]]  # return values of cossim for debugging

    ################################ For InstructScene END ################################

    @classmethod
    def from_dataset_directory(
        cls, dataset_directory, path_to_model_info, path_to_models
    ):
        objects = parse_threed_future_models(
            dataset_directory, path_to_models, path_to_model_info
        )
        return cls(objects)

    @classmethod
    def from_pickled_dataset(cls, path_to_pickled_dataset):
        with open(path_to_pickled_dataset, "rb") as f:
            dataset = pickle.load(f)
        return dataset


################################ For InstructScene BEGIN ################################

class ThreedFutureFeatureDataset(ThreedFutureDataset):
    def __init__(self, objects, objfeat_type: str):
        super().__init__(objects)

        self.objfeat_type = objfeat_type
        self.objfeat_dim = {
            "openshape_vitg14": 1280
        }[objfeat_type]

    def __getitem__(self, idx):
        obj = self.objects[idx]
        return {
            "jid": obj.model_jid,
            "objfeat": eval(f"obj.{self.objfeat_type}_features")
        }

    def collate_fn(self, samples):
        """
        Collate a list of samples into a batch while handling missing object features.

        Behavior:
        - By default, missing features (None) are replaced with a zero vector and
          an `objfeats_mask` tensor is returned where 1 means present and 0 means missing.
        - If you want different behavior, call this method with `missing_strategy` set to
          'mean' (replace with mean of available features) or 'drop' (drop samples with
          missing features).

        Returns a dict with keys:
        - 'jids': list[str]
        - 'objfeats': Tensor of shape (bs, objfeat_dim)
        - 'objfeats_mask': Tensor of shape (bs,) dtype uint8 (1 present, 0 missing)
        """

        # default strategy is 'zero' replacement; kept as an argument for flexibility
        return self._collate_with_missing_handling(samples, missing_strategy="zero")

    def _collate_with_missing_handling(self, samples, missing_strategy: str = "zero"):
        sample_batch = {
            "jids": [],     # str; (bs,)
            "objfeats": []  # list of arrays or None; will convert to Tensor
        }

        for sample in samples:
            sample_batch["jids"].append(str(sample["jid"]))
            feat = sample.get("objfeat", None)
            # convert torch.Tensor to numpy if needed
            if isinstance(feat, torch.Tensor):
                feat = feat.detach().cpu().numpy()
            if feat is None:
                sample_batch["objfeats"].append(None)
            else:
                sample_batch["objfeats"].append(np.asarray(feat, dtype=np.float32).reshape(-1))

        # If dropping missing samples
        if missing_strategy == "drop":
            keep_indices = [i for i, f in enumerate(sample_batch["objfeats"]) if f is not None]
            kept_jids = [sample_batch["jids"][i] for i in keep_indices]
            kept_feats = [sample_batch["objfeats"][i] for i in keep_indices]
            if len(kept_feats) == 0:
                raise ValueError("All samples are missing object features; cannot form a batch when using 'drop' strategy.")
            objfeats = torch.from_numpy(np.stack(kept_feats, axis=0)).float()
            mask = torch.ones(objfeats.shape[0], dtype=torch.uint8)
            return {"jids": kept_jids, "objfeats": objfeats, "objfeats_mask": mask}

        # construct replacement vectors
        zero_vec = np.zeros((self.objfeat_dim,), dtype=np.float32)
        available = [f for f in sample_batch["objfeats"] if f is not None]
        if len(available) == 0:
            mean_vec = zero_vec.copy()
        else:
            mean_vec = np.mean(np.stack(available, axis=0), axis=0)

        final_feats = []
        mask = []
        for f in sample_batch["objfeats"]:
            if f is None:
                if missing_strategy == "mean":
                    final_feats.append(mean_vec)
                else:
                    # default: zero
                    final_feats.append(zero_vec)
                mask.append(0)
            else:
                # ensure correct dimensionality; pad/truncate if necessary
                vec = np.asarray(f, dtype=np.float32).reshape(-1)
                if vec.shape[0] != self.objfeat_dim:
                    # try to handle minor mismatches by padding or truncating
                    if vec.shape[0] < self.objfeat_dim:
                        padded = np.zeros((self.objfeat_dim,), dtype=np.float32)
                        padded[: vec.shape[0]] = vec
                        vec = padded
                    else:
                        vec = vec[: self.objfeat_dim]
                final_feats.append(vec)
                mask.append(1)

        objfeats = torch.from_numpy(np.stack(final_feats, axis=0)).float()
        mask = torch.tensor(mask, dtype=torch.uint8)

        sample_batch["objfeats"] = objfeats
        sample_batch["objfeats_mask"] = mask
        return sample_batch

################################ For InstructScene END ################################
