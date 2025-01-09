import os
import sys
import argparse
from tkinter import Tk, filedialog
import json

import ipdb
import numpy as np
from matplotlib import cm
import matplotlib.pyplot as plt
from skimage import io, feature, color, transform

st = ipdb.set_trace

def read_image(path):
    image = io.imread(path)
    return image

def get_canny_edges(image, sigma):
    edges = feature.canny(color.rgb2gray(image), sigma=sigma)
    return edges

def get_hough_lines(edges, line_length, line_gap):
    lines = transform.probabilistic_hough_line(edges, line_length=line_length, line_gap=line_gap)
    return np.asarray(lines)

def visualize_inliers(image, edges, lines, inlier_lines_list, colors, fig_name='detected_lines.png'):
    subplot_count = len(inlier_lines_list) + 3

    fig, axes = plt.subplots(3, subplot_count-3, figsize=(15, 15), sharex=True, sharey=True)
    ax = axes.ravel()

    ax[0].imshow(image, cmap=cm.gray)
    ax[0].set_title('Input image')

    ax[1].imshow(edges, cmap=cm.gray)
    ax[1].set_title('Canny edges')

    ax[2].imshow(edges * 0)
    for line in lines:
        p0, p1 = line
        ax[2].plot((p0[0], p1[0]), (p0[1], p1[1]))
    ax[2].set_xlim((0, image.shape[1]))
    ax[2].set_ylim((image.shape[0], 0))
    ax[2].set_title('Probabilistic Hough')
    for i in range(len(inlier_lines_list)):
        ax[i+3].imshow(edges * 0)
        for line in lines[inlier_lines_list[i]]:
            p0, p1 = line
            ax[i+3].plot((p0[0], p1[0]), (p0[1], p1[1]), colors[i])
        ax[i+3].set_xlim((0, image.shape[1]))
        ax[i+3].set_ylim((image.shape[0], 0))
        ax[i+3].set_title('RANSAC {} Inliers'.format(str(i)))

    for a in ax:
        a.set_axis_off()

    plt.tight_layout()
    plt.savefig(fig_name)
    plt.close()

def visualize_vanishing_points(vp_height, vp_length, vp_width, image, lines, edges, inlier_lines_list, colors, fig_name):
    vps = [vp_height, vp_length, vp_width]
    for i in range(len(inlier_lines_list)):
        plt.imshow(image)
        for line in lines[inlier_lines_list[i]]:
            p0, p1 = line
            plt.plot((p0[0], p1[0]), (p0[1], p1[1]), colors[i])

        plt.plot([vps[i][0]], [vps[i][1]], colors[i]+'X', markersize=5)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(fig_name.split('.')[0] + str(i) + '.png') 
        plt.close()

    plt.imshow(image)
    for i in range(len(inlier_lines_list)):
        for line in lines[inlier_lines_list[i]]:
            p0, p1 = line
            plt.plot((p0[0], p1[0]), (p0[1], p1[1]), colors[i])

    plt.plot([vps[0][0]], [vps[0][1]], colors[0]+'X', markersize=5)
    plt.plot([vps[1][0]], [vps[1][1]], colors[1]+'X', markersize=5)
    plt.plot([vps[2][0]], [vps[2][1]], colors[2]+'X', markersize=5)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(fig_name) 
    plt.close() 

def calculate_metric_angle(current_hypothesis, lines, ignore_pts, ransac_angle_thresh):
    current_hypothesis = current_hypothesis / current_hypothesis[-1]
    hypothesis_vp_direction = current_hypothesis[:2] - lines[:,0]
    lines_vp_direction = lines[:,1] - lines[:,0]
    magnitude = np.linalg.norm(hypothesis_vp_direction, axis=1) * np.linalg.norm(lines_vp_direction, axis=1)
    magnitude[magnitude == 0] = 1e-5
    cos_theta = (hypothesis_vp_direction*lines_vp_direction).sum(axis=-1) / magnitude
    theta = np.arccos(np.abs(cos_theta))
    inliers = (theta < ransac_angle_thresh * np.pi / 180)
    inliers[ignore_pts] = False
    return inliers, inliers.sum()

def run_line_ransac(lines, ransac_iter, ransac_angle_thresh, ignore_pts=None):
    best_vote_count = 0
    best_inliers = None
    best_hypothesis = None
    if ignore_pts is None:
        ignore_pts = np.zeros((lines.shape[0])).astype('bool')
        lines_to_chose = np.arange(lines.shape[0])
    else:
        lines_to_chose = np.where(ignore_pts==0)[0]
    for iter_count in range(ransac_iter):
        idx1, idx2 = np.random.choice(lines_to_chose, 2, replace=False)
        l1 = np.cross(np.append(lines[idx1][1], 1), np.append(lines[idx1][0], 1))
        l2 = np.cross(np.append(lines[idx2][1], 1), np.append(lines[idx2][0], 1))

        current_hypothesis = np.cross(l1, l2)
        if current_hypothesis[-1] == 0:
            continue
        inliers, vote_count = calculate_metric_angle(current_hypothesis, lines, ignore_pts, ransac_angle_thresh)
        if vote_count > best_vote_count:
            best_vote_count = vote_count
            best_hypothesis = current_hypothesis
            best_inliers = inliers
    return best_hypothesis, best_inliers

def get_vp_inliers(image_path, sigma, iterations, line_len, line_gap, threshold):
    image = read_image(image_path)
    edges = get_canny_edges(image, sigma=sigma)
    lines = get_hough_lines(edges, line_length=line_len, line_gap=line_gap)

    best_hypothesis_1, best_inliers_1 = run_line_ransac(lines, iterations, threshold)
    ignore_pts = best_inliers_1
    best_hypothesis_2, best_inliers_2 = run_line_ransac(lines, iterations, threshold, ignore_pts=ignore_pts)
    ignore_pts = np.logical_or(best_inliers_1, best_inliers_2)
    best_hypothesis_3, best_inliers_3 = run_line_ransac(lines, iterations, threshold, ignore_pts=ignore_pts)
    inlier_lines_list = [best_inliers_1, best_inliers_2, best_inliers_3]
    best_hypothesis_1 = best_hypothesis_1 / best_hypothesis_1[-1]
    best_hypothesis_2 = best_hypothesis_2 / best_hypothesis_2[-1]
    best_hypothesis_3 = best_hypothesis_3 / best_hypothesis_3[-1]
    hypothesis_list = [best_hypothesis_1, best_hypothesis_2, best_hypothesis_3]
    viz_stuff = [image, edges, lines]
    return inlier_lines_list, hypothesis_list, viz_stuff

def main():
    # Initialisation de la boîte de dialogue pour choisir un fichier
    root = Tk()
    root.withdraw()  # Masquer la fenêtre principale de Tkinter
    
    image_path = filedialog.askopenfilename(title="Choisir une image",
                                            filetypes=[("Images", "*.jpg;*.jpeg;*.png;*.bmp")])
    if not image_path:
        raise ValueError("Aucune image sélectionnée. Veuillez relancer le script et sélectionner une image.")

    # Valeurs par défaut pour les paramètres
    sigma = 5  # Valeur par défaut pour canny_sigma
    iterations = 3000  # Valeur par défaut pour ransac_iter
    line_len = 11  # Longueur minimale des lignes pour Hough
    line_gap = 7  # Espace maximal entre les lignes pour Hough
    threshold = 2  # Seuil d'angle pour RANSAC

    # Traitement de l'image
    img_name = os.path.basename(image_path).split('.')[0]
    inlier_lines_list, hypothesis_list, viz_stuff = get_vp_inliers(
        image_path, sigma, iterations, line_len, line_gap, threshold
    )
    image, edges, lines = viz_stuff
    best_hypothesis_1, best_hypothesis_2, best_hypothesis_3 = hypothesis_list

    # Génération des noms de fichiers pour les visualisations
    fig_name_inliers = f"{img_name}_inliers_iter{iterations}_thresh{threshold}_sigma{sigma}_hlen{line_len}_hgap{line_gap}.png"
    fig_name_vanishing = f"{img_name}_vanishing_point_iter{iterations}_thresh{threshold}_sigma{sigma}_hlen{line_len}_hgap{line_gap}.png"

    colors = ['r', 'g', 'b']

    # Visualisation des résultats
    visualize_inliers(image, edges, lines, inlier_lines_list, colors, fig_name=fig_name_inliers)
    visualize_vanishing_points(
        best_hypothesis_1, best_hypothesis_2, best_hypothesis_3,
        image, lines, edges, inlier_lines_list, colors, fig_name_vanishing
    )

    # Génération du fichier JSON avec les coordonnées des points de fuite
    vanishing_points_data = {
        "vanishing_points": [
            {"vp_length": best_hypothesis_1[:2].tolist()},
            {"vp_height": best_hypothesis_2[:2].tolist()},
            {"vp_width": best_hypothesis_3[:2].tolist()}
        ]
    }
    json_file_name = f"vanishing_points.json"
    with open(json_file_name, "w") as json_file:
        json.dump(vanishing_points_data, json_file, indent=4)

    print(f"Résultats enregistrés\n")


if __name__ == "__main__":
    main()