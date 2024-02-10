import os
from lxml import etree
from datetime import datetime
import re


class MegaMekTimeline:
    def __init__(self):
        pass

    # Function to reduce a full name to a three-letter designation
    def get_designation(self,name):
        # Split the name into words
        words = name.split()

        #Remove the word "The" from the list
        if "The" in words:
            words.remove("The")

        # Extract the first letter of each word
        initials = [word[0] for word in words]

        # If the name has less than 3 words, add the first letter of the last word
        if len(initials) < 3:
            initials.append(words[-1][0])
        
        # If the initials are more than 3 only take the first 3
        if len(initials) > 3:
            initials = initials[:3]

        # Convert the initials to uppercase
        initials = [initial.upper() for initial in initials]
        # Concatenate the initials
        designation = ''.join(initials)
        # Return the designation
        return designation

    # Function to create an XML element for a news items
    def create_news_item_file(self,file_path, file_name):

        events = []
        
        file_name = file_name.split('.')[0]

        now = datetime.now()
        current_date = f"{now.month}/{now.day}/{now.year}"

        # Correctly handle the extraction process
        with open(file_path, 'r') as file:
            # Directly read the first line for the news network name
            news_network_name = file.readline().strip()
            # Convert to designation
            news_service_designation = self.get_designation(news_network_name)
            
            # Process the rest of the file for events
            for line in file:  # This continues from the second line
                line = line.strip()
                if line and ': ' in line:  # Check if the line is not empty and contains ': '
                    year, description = line.split(': ', 1)  # Split at the first occurrence of ': '
                    events.append((year, description))

        # Create the root element
        root = etree.Element('news')

        # Populate the XML with events
        for year, description in events:
            newsItem = etree.SubElement(root, 'newsItem')

            headline = etree.SubElement(newsItem, 'headline')
            headline.text = description

            date = etree.SubElement(newsItem, 'date')
            date.text = year

            desc = etree.SubElement(newsItem, 'desc')
            desc.text = ''
            #desc.text = etree.CDATA('')  # Wrap the description in CDATA tags

            # If the date is on or before 2107, set location to Terra amd news agency to TNS. Othyerwise, set it to the empty string or the specified news agency
            service = etree.SubElement(newsItem, 'service')
            location = etree.SubElement(newsItem, 'location')
            if year <= '2107':
                location.text = 'Terra'
                service.text = 'TNS'
            else:
                location.text = ''
                service.text = news_service_designation

        # Append the following comment to the XML content
        xml_comments = f'<?xml version="1.0" encoding="UTF-8"?>\n<!--\n{file_name}.xml\n2/9/2024\nMaurice Nelson (Travin)\nUpdated\n{current_date}\nThis file defines defines a set of news item that will display in the daily report frame of MekHQ. Sources are provided where available.\
    Here is a description of what goes in each newsItem tag.\n\
    headline - This is the headline that will appear in the daily report and in the title of the full article. This item should always be defined.\n\
    date - the date of the news item in yyyy-MM-dd format. This is required. If the "dd" part is missing, the day will be rolled randomly (each campaign will have its own random seed for that). Same if only the year is supplied. Finally, the year can be of the form "302X", which will generate a random day within that decade.\n\
    desc - a longer description of the news item. This is optional, but must be present for the "read more" link. It should always be surrounded by <![CDATA[stuff]]> and may contain html markup.\n\
    service - an optional tag for the news service doing the reporting\n\
    location - an optional tag for the location of the news report\n\
    -->\n\n'

        xml_str = xml_comments + etree.tostring(root, pretty_print=True, xml_declaration=False, encoding='UTF-8').decode()

        #print(xml_str)

        # Output the XML content to a file
        with open(f'./megamek_timelines/{file_name}.xml', 'w') as file:
            file.write(xml_str)

    def parse_date(self,date_str):
        # Try parsing the date in full yyyy-MM-dd format
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            try:
                # Try parsing the date in yyyy-MM format
                return datetime.strptime(date_str, "%Y-%m")
            except ValueError:
                try:
                    # If only the year is provided, treat it as January 1st of that year
                    return datetime.strptime(date_str, "%Y")
                except ValueError:
                    return datetime(1, 1, 1)  # Return a default very old date

    def combine_timelines(self, file_paths):
        # Create the root element for the combined XML document
        master_root = etree.Element('news')

        now = datetime.now()
        current_date = f"{now.month}/{now.day}/{now.year}"
        
        news_items = []

        # Iterate through each file path provided
        for file_path in file_paths:
            # Parse the XML file
            tree = etree.parse(file_path)
            root = tree.getroot()
            
            # Iterate through each child of the root (assuming 'newsItem')
            for child in root.findall('.//newsItem'):
                date_text = child.find('date').text if child.find('date') is not None else '0001'  # Use a default very old date
                date_obj = self.parse_date(date_text)
                news_items.append((date_obj, child))
                desc_element = child.find('desc')
                if desc_element.text is not None:
                    new_desc = etree.Element("desc")
                    new_desc.text = etree.CDATA(desc_element.text)
                    child.replace(desc_element, new_desc)
                
                #look for 2300 date
                if re.search(r'2300', date_text):
                    print(f'Found 2300 date in {file_path} at {date_text}')

        # Sort news items by their parsed date
        news_items.sort(key=lambda x: x[0])

        # Append sorted news items to master_root
        for _, item in news_items:
            #master_root.append(etree.fromstring(etree.tostring(item)))
            master_root.append(item)
        
        # Append the following comment to the XML content
        xml_comments = f'<?xml version="1.0" encoding="UTF-8"?>\n<!--\nnews.xml\n2/9/2024\nMaurice Nelson (Travin)\nUpdated\n{current_date}\nThis file defines defines a set of news item that will display in the daily report frame of MekHQ. Sources are provided where available.\
    Here is a description of what goes in each newsItem tag.\n\
    headline - This is the headline that will appear in the daily report and in the title of the full article. This item should always be defined.\n\
    date - the date of the news item in yyyy-MM-dd format. This is required. If the "dd" part is missing, the day will be rolled randomly (each campaign will have its own random seed for that). Same if only the year is supplied. Finally, the year can be of the form "302X", which will generate a random day within that decade.\n\
    desc - a longer description of the news item. This is optional, but must be present for the "read more" link. It should always be surrounded by <![CDATA[stuff]]> and may contain html markup.\n\
    service - an optional tag for the news service doing the reporting\n\
    location - an optional tag for the location of the news report\n\
    -->\n\n'

        # Convert the master_root Element back to a string, prepend the declaration and comments, and ensure pretty printing
        master_xml_str = xml_comments + etree.tostring(master_root, pretty_print=True, xml_declaration=False, encoding='UTF-8').decode()

        return master_xml_str

    def run(self,sarna_dir='./sarna_timelines', megamek_dir='./megamek_timelines'):
        # For each file in ./sarna_timelines run the function create_news_item_file
        for file in os.listdir('./sarna_timelines'):
            if file.endswith('.txt'):
                self.create_news_item_file(f'{sarna_dir}/{file}', file)

        file_paths = [f'{megamek_dir}/{file}' for file in os.listdir(megamek_dir) if file.endswith('.xml')]
        master_xml_str = self.combine_timelines(file_paths)

        # Write the combined XML string to a new file and show a preview of the content
        master_file_path_with_format = 'news.xml'
        with open(master_file_path_with_format, 'w') as file:
            file.write(master_xml_str)