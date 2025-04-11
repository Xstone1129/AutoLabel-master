import os
import json

def json_to_txt(json_path, output_dir):
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    shapes = data['shapes']
    image_width = data['imageWidth']
    image_height = data['imageHeight']
    
    txt_lines = []
    for shape in shapes:
        label = shape['label']  # Assuming 'label' field exists in JSON
        points = shape['points']
        # Convert points from absolute to relative coordinates
        rel_points = [(point[0] / image_width, point[1] / image_height) for point in points]
        
        # Format the line in the required format
        line = f"{label} {' '.join([f'{x:.3f}' for p in rel_points for x in p])}"
        txt_lines.append(line)
    
    # Create output file name based on input JSON file name
    json_filename = os.path.basename(json_path)
    txt_filename = os.path.splitext(json_filename)[0] + '.txt'
    txt_path = os.path.join(output_dir, txt_filename)
    
    # Write to TXT file
    with open(txt_path, 'w') as f:
        f.write('\n'.join(txt_lines))
    
    print(f"Converted {json_path} to {txt_path}")

def batch_convert_json_to_txt(input_folder, output_folder):
    # Ensure output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Iterate over all files in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith('.json'):
            json_path = os.path.join(input_folder, filename)
            json_to_txt(json_path, output_folder)

# Example usage
if __name__ == "__main__":
    input_folder = '/home/xiao/SH_data/AutoLabel-master/data/labels'
    output_folder = '/home/xiao/SH_data/AutoLabel-master/data/images'  # Specify your output folder here
    batch_convert_json_to_txt(input_folder, output_folder)
