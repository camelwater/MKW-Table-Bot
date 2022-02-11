'''
Created on Aug 2, 2020

@author: willg
'''
import cv2
import numpy as np
from PIL import Image, ImageFont, ImageDraw
from typing import List, Tuple
from TableBot import ChannelBot
import Mii
import UtilityFunctions
import common



#================ Miis on table ====================
#General footer constants
MINIMUM_TABLE_WIDTH = 860
FOOTER_HEIGHT = 160
DEFAULT_FOOTER_HORIZONTAL_BORDER_COLOR = np.array([255,255,255], dtype=np.uint8)
DEFAULT_FOOTER_HORIZONTAL_BORDER_HEIGHT = 4
SHOULD_REFLECT_WITH_TEAMS = False

#Mii picture constants
MII_PADDING_INSIDE_SECTION = -10
MII_PADDING_SECTION_LEFT = 7
MII_PADDING_SECTION_RIGHT = 7

#Team tag text constants
TEAM_TAG_TEXT_COLOR = (255,255,255)
DEFAULT_TEAM_TAG_FONT = f"{common.FONT_PATH}Roboto-Medium.ttf"
MAX_TEAM_TAG_HEIGHT_BOX = 50
TEAM_TAG_TEXT_MAX_HEIGHT = 30
TEAM_TAG_WIDTH_PADDING = 15
TEAM_TAG_CHAR_SET_TO_INCREASE_SIZE = {'j', 'g', 'y', 'q', 'p'}
FONT_CORRECTIVE_HEIGHT_OFFSET = -3

assert MAX_TEAM_TAG_HEIGHT_BOX > TEAM_TAG_TEXT_MAX_HEIGHT

#Mii name text constants
MII_NAME_TEXT_COLOR = (255,255,255)
DEFAULT_MII_NAME_FONT = f"{common.FONT_PATH}Roboto-Medium.ttf"
MII_NAME_WIDTH_PADDING = 5
MII_NAME_CHAR_SET_TO_INCREASE_SIZE = {'j', 'g', 'y', 'q', 'p'}
MAX_MII_NAME_HEIGHT_BOX = 36
MII_NAME_TEXT_MAX_HEIGHT = 18
MII_NAME_BASE_Y_LOCATION = MAX_TEAM_TAG_HEIGHT_BOX




#Individual team footer section variables
TEAM_LEFT_BORDER_WIDTH = 1
TEAM_LEFT_BORDER_COLOR = np.array([255,255,255], dtype=np.uint8)


MAX_FONT_ITERATIONS = 20

TESTING_IMAGE = "851185374897504276.png"


AUTOGENERATED_FILE_NAME = "AutoGenerateHeader.png"
ERRORS_HEADER_FILE_NAME = "ErrorsHeader.png"
EDITS_HEADER_FILE_NAME = "EditsHeader.png"
NO_ERRORS_HEADER_FILE_NAME = "NoErrorsHeader.png"

AUTOGENERATED_HEADER_PATH = f"{common.TABLE_HEADERS_PATH}{AUTOGENERATED_FILE_NAME}"
ERRORS_HEADER_PATH = f"{common.TABLE_HEADERS_PATH}{ERRORS_HEADER_FILE_NAME}"
EDITS_HEADER_PATH = f"{common.TABLE_HEADERS_PATH}{EDITS_HEADER_FILE_NAME}"
NO_ERRORS_HEADER_PATH = f"{common.TABLE_HEADERS_PATH}{NO_ERRORS_HEADER_FILE_NAME}"


def create_numpy_image_with_color(dimensions, color):
    image = np.empty((*dimensions, len(color)), dtype=np.uint8)
    image[:] = color
    return image

#Takes a footer (pillow image) and a path to the table, adds the footer to the bottom of the table and saves the table in the specified location
#If the footer has a smaller width than the table, the left and right part of the footer are extended by an equal amount - the color of the extension is based on the left and right edges
#If the footer has a larger width than the table, the left and right are cropped by an equal amount
#Therefore, it is suggested that everything in the footer is centered in case it is cropped.
def add_autotable_footer(footer, table_image_path=TESTING_IMAGE, out_image_path="combined_test.png", extension_should_reflect=True):
    table_cv2 = cv2.imread(table_image_path)
    table_width = len(table_cv2[0])
    
    footer_width, footer_height = len(footer[0]), len(footer)
    footer_array = footer

    # Setting the points for cropped image
    if footer_width > table_width:
        """
        excess_width = footer_width - table_width
        left = excess_width//2
        right = footer_width - (excess_width - left)
        footer_array = footer_array[0:len(footer_array),left:right]
        """
        #instead of cutting off, resize
        scale_ratio = table_width / footer_width
        height = int(footer_height * scale_ratio)
        dim = (table_width, height)
        footer_array = cv2.resize(footer_array, dim, interpolation = cv2.INTER_AREA)
    elif footer_width < table_width:
        add_left_footer = int((table_width - footer_width)/2)
        add_right_footer = int(table_width - (add_left_footer + footer_width))
        if add_left_footer < 1 or add_right_footer < 1:
            return False
        if SHOULD_REFLECT_WITH_TEAMS and extension_should_reflect:
            left_footer_extend = footer_array[:, 0]
            right_footer_extend = footer_array[:, -1]

            left_data = np.tile(left_footer_extend, (add_left_footer, 1))
            left_data = left_data.reshape((left_footer_extend.shape[0], add_left_footer , 3), order='F')
            right_data = np.tile(right_footer_extend, (add_right_footer, 1))
            right_data = right_data.reshape((right_footer_extend.shape[0], add_right_footer, 3), order='F')
            footer_array = np.concatenate((left_data, footer_array, right_data), axis=1)
            
        else:      
            left_footer_extend = footer_array[0][0]
            right_footer_extend = footer_array[-1][-1]
            
            left_data = np.full((footer_height, add_left_footer, 3), left_footer_extend)
            right_data = np.full((footer_height, add_right_footer, 3), right_footer_extend)
            footer_array = np.concatenate((left_data, footer_array, right_data), axis=1)
    else:
        pass
    
    total_combined = np.concatenate((table_cv2, footer_array), axis=0)
    cv2.imwrite(out_image_path, total_combined)
    return True

#Takes team scores and adds the miis to the table
#The exact structure of team_scores can be found in ScoreKeeper.get_war_table_DCS, but as of 6/7/2021, the structure as the following:
#A list of tuples. Tuples have 2 pieces of data. The first is a str which is the team tag. The 2nd is a list of tuples (a tuple contains information about that player on the team).
#The first index of that tuple is the players FC, the 2nd index of that tuple is a tuple if 2 length. The first index of that tuple is the table str for Lorenzi's website, the 2nd index is their total score, including penalties.
def add_miis_to_table(channel_bot:ChannelBot, team_scores:List[Tuple[str, List[Tuple[str, Tuple[str, int]]]]], table_image_path=TESTING_IMAGE, out_image_path="combined_test.png"):
    if common.MIIS_ON_TABLE_DISABLED:
        return True
    extension_reflect, mii_footer = get_footer_with_miis(channel_bot, team_scores)
    return add_autotable_footer(mii_footer, table_image_path=table_image_path, out_image_path=out_image_path, extension_should_reflect=extension_reflect)
    

def get_footer_with_miis(channel_bot:ChannelBot, team_scores:List[Tuple[str, List[Tuple[str, Tuple[str, int]]]]]):
    
    team_footers = []
    extension_should_reflect = not channel_bot.getWar().is_ffa()
    if channel_bot.getWar().is_ffa():
        all_miis = {}
        for team_tag, team_players in team_scores:
            available_miis = channel_bot.room.get_available_miis_dict([player_data[0] for player_data in team_players])
            for mii_key, mii_value in available_miis.items():
                all_miis[mii_key] = mii_value
        if len(all_miis) > 0:
            team_footers.append(("FFA", generate_footer_section_for_team(all_miis, "FFA")))
    else:
        for team_tag, team_players in team_scores:
            available_miis = channel_bot.room.get_available_miis_dict([player_data[0] for player_data in team_players])
            should_add_left_border = len(team_footers) > 0 #There's already one team footer, so add left border
            if len(available_miis) > 0:
                team_footers.append((team_tag, generate_footer_section_for_team(available_miis, team_tag, add_left_border=should_add_left_border)))
        
    if len(team_footers) > 0:
        total_footer = np.concatenate([tf[1] for tf in team_footers], axis=1)
        total_footer = insert_border_below_teams(total_footer)
        return extension_should_reflect, total_footer
    else:
        return extension_should_reflect, get_blank_autotable_footer()
            
        #constant= cv.copyMakeBorder(img1,10,10,10,10,cv.BORDER_CONSTANT,value=BLUE)

def insert_border_below_teams(footer, border_color=DEFAULT_FOOTER_HORIZONTAL_BORDER_COLOR, border_height=DEFAULT_FOOTER_HORIZONTAL_BORDER_HEIGHT):
    team_tag_section = footer[:MAX_TEAM_TAG_HEIGHT_BOX]
    lower_section = footer[MAX_TEAM_TAG_HEIGHT_BOX:]
    footer_width = len(footer[0])
    middle_border = create_numpy_image_with_color(dimensions=(border_height, footer_width), color=border_color)
    return np.concatenate([team_tag_section, middle_border, lower_section], axis=0)

def get_blank_autotable_footer(height=FOOTER_HEIGHT, color=common.DEFAULT_FOOTER_COLOR):
    return create_numpy_image_with_color(dimensions=(height, MINIMUM_TABLE_WIDTH), color=color)


def generate_footer_section_for_team(miis:List[Mii.Mii], team_tag="No Tag", height=FOOTER_HEIGHT, background_color=common.DEFAULT_FOOTER_COLOR, forced_mii_dimension=common.MII_SIZE_FOR_TABLE, add_left_border=False):
    mii_dimension = forced_mii_dimension
    mii_padding_inside = MII_PADDING_INSIDE_SECTION
    mii_padding_outside_left = MII_PADDING_SECTION_LEFT
    mii_padding_outside_right = MII_PADDING_SECTION_RIGHT
    
    #Compute total section width for this team
    section_width = (len(miis) * mii_dimension) + ((len(miis)-1) * mii_padding_inside) + mii_padding_outside_left + mii_padding_outside_right
    
    #Create background
    blank_footer_background_array = create_numpy_image_with_color(dimensions=(height, section_width), color=background_color)

    #Place each mii cv2 in correct location on blank footer background array
    for index, mii in enumerate(miis.values()):
        mii_start_location_x = mii_padding_outside_left + (index * (mii_dimension + mii_padding_inside))
        mii_end_location_x = mii_start_location_x + mii_dimension
        mii_start_location_y = height - mii_dimension
        mii_end_location_y = mii_start_location_y + mii_dimension
        
        mii_image = mii.get_table_mii_picture_cv2()
        
        if mii_image is None: #Skip placing this mii on the canvas if we couldn't get the cv2 image for it
            continue
        blank_footer_background_array[mii_start_location_y:mii_end_location_y,mii_start_location_x:mii_end_location_x] = mii_image[:,:,0:-1]

    #Convert array into a format that we can put text on

    pil_image = Image.fromarray(blank_footer_background_array)
    canvas_for_text = ImageDraw.Draw(pil_image)
    #Put mii names on footer, above the mii pictures
    for index, mii in enumerate(miis.values()):
        mii_name = mii.lounge_name if mii.lounge_name != "" else UtilityFunctions.process_name(mii.mii_name)
        mii_name_start_location_x = mii_padding_outside_left + (index * (mii_dimension + mii_padding_inside))
        mii_name_end_location_x = mii_name_start_location_x + mii_dimension
        mii_name_start_location_y = MII_NAME_BASE_Y_LOCATION
        
        actual_mii_picture_width = mii_dimension + mii_padding_inside
        mii_font_size = 20
        max_mii_name_height = MII_NAME_TEXT_MAX_HEIGHT
        should_increase_mii_name_size = any(True for letter in MII_NAME_CHAR_SET_TO_INCREASE_SIZE if letter in mii_name)
        if should_increase_mii_name_size:
            max_mii_name_height += 4
        mii_font = ImageFont.truetype(DEFAULT_MII_NAME_FONT, mii_font_size)
        for _ in range(MAX_FONT_ITERATIONS):
            if mii_font.getsize(mii_name)[0] > (actual_mii_picture_width - MII_NAME_WIDTH_PADDING) and mii_font.getsize(mii_name)[1] <= max_mii_name_height:
                #should_increase_mii_name_size = True
                pass
            if mii_font.getsize(mii_name)[0] <= (actual_mii_picture_width - MII_NAME_WIDTH_PADDING) and mii_font.getsize(mii_name)[1] <= max_mii_name_height:
                break
                 
            # iterate until the text size is just larger than the criteria
            mii_font_size -= 1
            mii_font = ImageFont.truetype(DEFAULT_MII_NAME_FONT, mii_font_size)
            
        
        mii_name_width = mii_font.getsize(mii_name)[0]
        mii_name_height = mii_font.getsize(mii_name)[1]
        mii_name_padding_width = mii_name_end_location_x - mii_name_start_location_x - mii_name_width
        mii_name_padding_height = MAX_MII_NAME_HEIGHT_BOX - mii_name_height 
        mii_name_start_location_x += round(mii_name_padding_width / 2)
        mii_name_start_location_y += round(mii_name_padding_height / 2)
        if should_increase_mii_name_size:
            mii_name_start_location_y += 2
        
        canvas_for_text.text((mii_name_start_location_x,mii_name_start_location_y), mii_name, MII_NAME_TEXT_COLOR, font=mii_font)
    
    #Put team name on footer, centered above mii names
    team_tag = UtilityFunctions.process_name(team_tag)
    team_tag_font_size = 30
    _team_tag_max_height = TEAM_TAG_TEXT_MAX_HEIGHT
    should_increase_team_tag_size = any(True for letter in TEAM_TAG_CHAR_SET_TO_INCREASE_SIZE if letter in team_tag)
    if should_increase_team_tag_size:
        _team_tag_max_height += 4
    team_tag_font = ImageFont.truetype(DEFAULT_TEAM_TAG_FONT, team_tag_font_size)
    for _ in range(MAX_FONT_ITERATIONS):
        if team_tag_font.getsize(team_tag)[0] <= (section_width - TEAM_TAG_WIDTH_PADDING) and team_tag_font.getsize(team_tag)[1] <= _team_tag_max_height:
            break
        # iterate until the text size is just larger than the criteria
        team_tag_font_size -= 1
        team_tag_font = ImageFont.truetype(DEFAULT_TEAM_TAG_FONT, team_tag_font_size)
    #Compute location of team name
    team_tag_width = team_tag_font.getsize(team_tag)[0]
    team_tag_height = team_tag_font.getsize(team_tag)[1]
    team_tag_padding_height = MAX_TEAM_TAG_HEIGHT_BOX - team_tag_height
    team_tag_start_location_x = (section_width - team_tag_width)//2
    team_tag_start_location_y = round(team_tag_padding_height / 2)
    if should_increase_team_tag_size:
        team_tag_start_location_y += 2
        
    team_tag_start_location_y += FONT_CORRECTIVE_HEIGHT_OFFSET
        
    canvas_for_text.text((team_tag_start_location_x-1,team_tag_start_location_y), team_tag, TEAM_TAG_TEXT_COLOR, font=team_tag_font)


    blank_footer_background_array = np.array(pil_image)
    if add_left_border:
        left_border = create_numpy_image_with_color(dimensions=(len(blank_footer_background_array), TEAM_LEFT_BORDER_WIDTH), color=TEAM_LEFT_BORDER_COLOR)
        blank_footer_background_array = np.concatenate((left_border, blank_footer_background_array), axis=1)                                 
        
    return blank_footer_background_array
        

def add_autotable_header(errors=True, table_image_path="TEST_TABLE.png", autogenerate_image_path=AUTOGENERATED_HEADER_PATH, errors_image_path=ERRORS_HEADER_PATH, no_errors_image_path=NO_ERRORS_HEADER_PATH, out_image_path="combined_test.png", edits=False, edits_image_path=EDITS_HEADER_PATH):
    autogenerate_header_cv2 = cv2.imread(autogenerate_image_path)
    autogenerate_extend = autogenerate_header_cv2[0][0]
    table_cv2 = cv2.imread(table_image_path)
    
    
    middle_header_cv2 = None
    if edits:
        middle_header_cv2 = cv2.imread(edits_image_path)
    elif errors:
        middle_header_cv2 = cv2.imread(errors_image_path)
    else:
        middle_header_cv2 = cv2.imread(no_errors_image_path)
    middle_header_extend = middle_header_cv2[0][0]
    
    
    
    autogenerate_header_height = len(autogenerate_header_cv2)
    autogenerate_header_width = len(autogenerate_header_cv2[0])
    middle_header_height = len(middle_header_cv2)
    middle_header_width = len(middle_header_cv2[0])
    table_width = len(table_cv2[0])
    
    add_left_autogenerate = int((table_width - autogenerate_header_width)/2)
    add_right_autogenerate = int(table_width - (add_left_autogenerate + autogenerate_header_width))
    
    add_left_middle = int((table_width - middle_header_width)/2)
    add_right_middle = int(table_width - (add_left_middle + middle_header_width))
    
    if add_left_autogenerate > 0 and add_right_autogenerate > 0: 
        left_data = np.full((autogenerate_header_height, add_left_autogenerate, 3), autogenerate_extend)
        right_data = np.full((autogenerate_header_height, add_right_autogenerate, 3), autogenerate_extend)
        autogenerate_header_cv2 = np.concatenate((left_data, autogenerate_header_cv2, right_data), axis=1)
    elif add_left_autogenerate < 0 or add_right_autogenerate < 0:
        return False
    
    
    
    if add_left_middle > 0 and add_right_middle > 0:
        left_data = np.full((middle_header_height, add_left_middle, 3), middle_header_extend)
        right_data = np.full((middle_header_height, add_right_middle, 3), middle_header_extend)
        middle_header_cv2 = np.concatenate((left_data, middle_header_cv2, right_data), axis=1)
    
    elif add_left_middle < 0 or add_right_middle < 0:
        return False
    
    total_combined = np.concatenate((autogenerate_header_cv2, middle_header_cv2, table_cv2), axis=0)
    cv2.imwrite(out_image_path, total_combined)
    return True

