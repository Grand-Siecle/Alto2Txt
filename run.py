import os
import zipfile
from lxml import etree
from tqdm import tqdm
import click

def extract_zip(zip_file, extract_to):
    """Extracts all XML files from the ZIP archive to the specified directory."""
    xml_files = []
    with zipfile.ZipFile(zip_file, 'r') as zf:
        for file_info in tqdm(zf.infolist(), desc="Extracting XML files"):
            if file_info.filename.endswith('.xml'):
                zf.extract(file_info, extract_to)
                xml_files.append(os.path.join(extract_to, file_info.filename))
    return xml_files

def extract_content_from_alto(xml_file):
    """Extracts the content from <String> elements in an ALTO XML file and formats it into sentences."""
    content_list = []
    try:
        tree = etree.parse(xml_file)
        for string in tree.xpath('//ns:String', namespaces={'ns': 'http://www.loc.gov/standards/alto/ns-v4#'}):
            content = string.get('CONTENT')
            if content:
                content_list.append(content)
    except Exception as e:
        print(f"Error processing {xml_file}: {e}")
    return content_list

def create_text_file(content_list, text_file):
    """Creates a text file with the extracted content, formatted into sentences."""
    with open(text_file, 'w', encoding='utf-8') as f:
        sentence = []
        previous_word = ""
        
        for word in content_list:
            if previous_word.endswith('¬'):
                previous_word = previous_word.replace('¬', '') + word
            else:
                if previous_word:
                    sentence.append(previous_word)
                previous_word = word
            
            if previous_word.endswith('.'):
                sentence.append(previous_word)
                f.write(" ".join(sentence) + "\n")
                sentence = []
                previous_word = ""
        
        if previous_word:
            sentence.append(previous_word)
        if sentence:
            f.write(" ".join(sentence) + "\n")

def cleanup_xml_files(folder):
    """Removes all XML files in the specified folder."""
    for file_name in os.listdir(folder):
        if file_name.endswith('.xml'):
            file_path = os.path.join(folder, file_name)
            os.remove(file_path)
    print("All XML files have been removed.")


@click.command()
@click.argument('zip_file', type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.option('--output-folder', type=click.Path(), default='.', help='Directory to save the extracted text file.')          
def main(zip_file, output_folder):
    """Main function to process the ZIP file containing ALTO XML files."""
    # Step 1: Extract XML files from the ZIP
    xml_files = extract_zip(zip_file, output_folder)
    
    basename = os.path.splitext(os.path.basename(zip_file))[0]
    
    all_contents = []
    
    # Step 2: Extract contents from each ALTO file with progress bar
    for xml_file in tqdm(xml_files, desc="Processing XML files"):
        contents = extract_content_from_alto(xml_file)
        all_contents.extend(contents)
    
    # Step 3: Create a text file with all contents formatted into sentences
    text_file = os.path.join(output_folder, basename + '.txt')
    create_text_file(all_contents, text_file)
    
    cleanup_xml_files(output_folder)
    
    print(f"Extracted content saved to: {text_file}")

if __name__ == "__main__":
    main()