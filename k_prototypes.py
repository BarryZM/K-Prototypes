# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 15:18:14 2020
k-prototypes 聚类算法的实现
@author: zhenyu wu
"""
import pandas as pd
import numpy as np
from sklearn import preprocessing
from sklearn import metrics
from sklearn.manifold import TSNE
from kmodes.kprototypes import KPrototypes


DEMO = True
N = 5


def Load_Data(demo=DEMO):
    """
    加载测试数据集
    
    Parameters
    ----------
    demo : bool值 
        是否仅加载测试数据
        
    Returns
    -------
    data : DataFrame
        特征分离后的数据集
    data_id : list
        事件编号
    len(numerical_features) : int
        数值特征个数
    len(category_features) : int
        类别特征个数
    """
    data = pd.read_csv('../data/clean_data.csv', low_memory=False)
    data = data.drop(columns=['Unnamed: 0'])
    data = data.sample(frac=1, random_state=2020).reset_index(drop=True)
    data_id = list(data['eventid'])
    numerical_features = ['latitude', 'longitude', 'nperps', 'nperpcap', 'nkill', 'nkillus', 
                          'nkillter', 'nwound', 'nwoundus', 'nwoundte', 'nhostkid', 'nhostkidus', 
                          'nkill_nwound', 'nkill_nwound_us', 'nkill_nwound_dte', 'kill_perct', 
                          'wound_perct', 'nkill_perct', 'scite_count', ]
    category_features = ['extended', 'country', 'region', 'specificity', 'vicinity', 'crit1', 
                         'crit2', 'crit3', 'doubtterr', 'alternative', 'multiple', 'success', 
                         'suicide', 'attacktype1', 'attacktype2', 'targtype1', 'targsubtype1', 
                         'natlty1', 'guncertain1', 'individual', 'claimed', 'claimmode', 
                         'weaptype1', 'weapsubtype1', 'property', 'propextent', 'ishostkid', 
                         'INT_LOG', 'INT_IDEO', 'INT_MISC', 'INT_ANY', 'iyear', 'imonth', 'iday', ]
    data = data[numerical_features+category_features]
    if demo:
        num_data = 300
        data = data[:num_data]
        data_id = data_id[:num_data]
    numerical_data = data[numerical_features]
    # 对连续特征进行归一化处理
    min_max_scaler = preprocessing.MinMaxScaler()
    numerical_data = pd.DataFrame(min_max_scaler.fit_transform(numerical_data))
    numerical_data.columns = numerical_features
    category_data = data[category_features]
    data = pd.concat([numerical_data, category_data], axis=1)
    return data, data_id, len(numerical_features), len(category_features)


def Calculate_Single_Distance(num_data, cat_data, num_center, cat_center):
    """
    计算两个样本之间的距离

    Parameters
    ----------
    num_data : list
        数据样本中的连续数值部分
    cat_data : list
        数据样本中的类别型特征部分
    num_center : list
        聚类中心点的连续数值部分
    cat_center : list
        聚类中心点的类别特征部分
    num_numerical : float
        欧式距离权重
    num_category : float
        汉明距离权重
        
    Returns
    -------
    euclidean : float
        两个样本点之间的欧几里得距离
    hamming : float
        两个样本点之间的汉明距离
    """
    euclidean = np.linalg.norm(np.array(num_data)-np.array(num_center))
    hamming = np.shape(np.nonzero(np.array(cat_data)-np.array(cat_center))[0])[0]
    return euclidean, hamming
    

def Calculate_Center(data, n, num_numerical, num_category):
    """
    更新聚类中心点

    Parameters
    ----------
    data : DataFrame
        数据样本
    n : int
        聚类中心的个数，默认值为5
    num_numerical : int 
        数值特征个数
    num_category : int 
        类别特征个数

    Returns
    -------
    numerical_centers : DataFrame
        更新后的数值型特征的聚类中心点
    category_centers : DataFrame
        更新后的类别型特征的聚类中心点
    """
    numerical_centers = []
    category_centers = []
    for i in range(n):
        sub_data = data.loc[data.label==i]
        sub_data_numerical = sub_data.iloc[:, :num_numerical]
        sub_data_category = sub_data.iloc[:, num_numerical:-1]
        numerical_center = []
        for col in sub_data_numerical.columns:
            numerical_center.append(sub_data_numerical[col].mean())
        numerical_centers.append(numerical_center)
        category_center = []
        for col in sub_data_category.columns:
            category_center.append(list(sub_data_category[col].mode())[0])
        category_centers.append(category_center)
    numerical_centers = pd.DataFrame(numerical_centers)
    numerical_centers.columns = sub_data_numerical.columns
    category_centers = pd.DataFrame(category_centers)
    category_centers.columns = sub_data_category.columns
    return numerical_centers, category_centers
            
    
def K_Prototypes(random_seed, n, data, num_numerical, num_category, max_iters, mode):
    """
    K_Prototypes混合聚类算法

    Parameters
    ----------
    n : int
        聚类中心的个数
    data : DataFrame
        被聚类的样本
    random_seed : int 
        随机数种子
    num_numerical : int 
        数值特征个数
    num_category : int 
        类别特征个数
    max_iters : int 
        最大迭代次数
    mode : int 
        计算模式
        
    Returns
    -------
    newlabel : list
        最终的聚类结果
    center_numerical : DataFrame
        数值型特征的聚类中心点
    center_category : DataFrame
        类别型特征的聚类中心点
    """
    all_features = num_numerical+num_category
    # 当belta=0时，本算法为kmeans聚类
    # 当alpha=0时，本算法为kmodes聚类
    if mode==1:
        alpha = 0
        belta = 1
        print('K_Modes聚类')
    elif mode==2:
        alpha = 1
        belta = 0
        print('K_Means聚类')
    else:
        alpha = num_numerical/all_features
        belta = num_category/all_features
        print('K_Prototypes聚类')
    # 随机选定n个初始聚类中心点
    init_center_points = data.sample(n=n, replace=False, random_state=random_seed, axis=0)
    # 对数据特征按照类别进行划分
    numerical_data = data.iloc[:, :num_numerical]
    category_data = data.iloc[:, num_numerical:]
    init_center_numerical = init_center_points.iloc[:, :num_numerical]
    init_center_category = init_center_points.iloc[:, num_numerical:]
    # 计算每个样本到各个聚类中心簇的距离
    label = []
    for i in range(len(data)):
        all_distance = []
        euclidean = []
        hamming = []
        for j in range(n):
            sig_euclidean, sig_hamming = Calculate_Single_Distance(
                numerical_data.iloc[[i]].values[0], 
                category_data.iloc[[i]].values[0], 
                init_center_numerical.iloc[[j]].values[0], 
                init_center_category.iloc[[j]].values[0],)
            euclidean.append(sig_euclidean)
            hamming.append(sig_hamming)
        for j in range(n):
            distance = alpha*euclidean[j]/sum(euclidean)+belta*hamming[j]/sum(hamming)
            all_distance.append(distance)
        label.append(np.argmin(np.array(all_distance)))
    data['label'] = label
    # 迭代更新聚类中心部分
    err_distance = 1
    iter_count = 0
    while iter_count<=max_iters and err_distance!=0:
        iter_count += 1
        center_numerical, center_category = Calculate_Center(data, n, num_numerical, num_category)
        newlabel = []
        for i in range(len(data)):
            all_distance = []
            euclidean = []
            hamming = []
            for j in range(n):
                sig_euclidean, sig_hamming = Calculate_Single_Distance(
                    numerical_data.iloc[[i]].values[0], 
                    category_data.iloc[[i]].values[0], 
                    center_numerical.iloc[[j]].values[0], 
                    center_category.iloc[[j]].values[0],)
                euclidean.append(sig_euclidean)
                hamming.append(sig_hamming)
            for j in range(n):
                distance = alpha*euclidean[j]/sum(euclidean)+belta*hamming[j]/sum(hamming)
                all_distance.append(distance)
            newlabel.append(np.argmin(np.array(all_distance)))
        err_distance = np.shape(np.nonzero(np.array(list(data['label']))-np.array(newlabel))[0])[0]
        data['label'] = newlabel
    print(data['label'].value_counts())
    print('最终的迭代次数为：{}'.format(iter_count))
    data.drop('label', axis=1, inplace=True)
    return newlabel, center_numerical, center_category
    

if __name__ == '__main__':
    data, data_id, num_numerical_features, num_category_features = Load_Data()
    label_1, center_numerical_1, center_category_1 = K_Prototypes(random_seed=2020, n=N, data=data, 
                                                            num_numerical=num_numerical_features, 
                                                            num_category=num_category_features, 
                                                            max_iters = 10, mode=3)
    print("K_Prototypes算法的Calinski-Harabaz Index值为：{}".format(metrics.calinski_harabasz_score(data, label_1)))
    label_2, center_numerical_2, center_category_2 = K_Prototypes(random_seed=2020, n=N, data=data, 
                                                            num_numerical=num_numerical_features, 
                                                            num_category=num_category_features, 
                                                            max_iters = 10, mode=2)
    print("K_Means算法的Calinski-Harabaz Index值为：{}".format(metrics.calinski_harabasz_score(data, label_2)))
    label_3, center_numerical_3, center_category_3 = K_Prototypes(random_seed=2020, n=N, data=data, 
                                                            num_numerical=num_numerical_features, 
                                                            num_category=num_category_features, 
                                                            max_iters = 10, mode=1)
    print("K_Modes算法的Calinski-Harabaz Index值为：{}".format(metrics.calinski_harabasz_score(data, label_3)))
    kp = KPrototypes(n_clusters=5, init='Huang', n_init=1, verbose=True, n_jobs=4, random_state=2020)
    KPrototypes_results = kp.fit_predict(data, categorical=list(range(num_numerical_features, num_numerical_features+num_category_features-1)))
    print("K_Prototypes算法包的Calinski-Harabaz Index值为：{}".format(metrics.calinski_harabasz_score(data, KPrototypes_results)))
