import cv2, os, glob
def preprocess_images(input_dir="/data/raw/images", output_dir="/data/processed/cv"):
    os.makedirs(output_dir, exist_ok=True)
    for img_path in glob.glob(f"{input_dir}/*.jpg"):
        img = cv2.imread(img_path)
        img = cv2.resize(img, (224, 224))
        cv2.imwrite(os.path.join(output_dir, os.path.basename(img_path)), img)
    print("✅ CV preprocessing done.")

if __name__ == "__main__":
    preprocess_images()
