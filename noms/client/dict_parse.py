import operator
from ..objects.food import Food

def search_parse(search_results):
    """ Return a simplified version of the json object returned from the USDA API.
    This deletes extraneous pieces of information that are not important for providing
    context on the search results.
    """
    if 'errors' in search_results.keys():
        return None
    # Store the search term that was used to produce these results
    search_term = search_results["foodSearchCriteria"]["generalSearchInput"]
    # Store a list of dictionary items for each result of the search
    return dict(search_term=search_term, items=search_results)

def food_parse(food_results, nutrient_dict, values):
    """ Return a simplified version of the json object returned from the USDA API.
    This deletes extraneous pieces of information, including nutrients that are
    not tracked. It also exchanges nutrient names for their more common names, or "nicknames",
    as defined in noms.objects.nutrient_dict
    """
    if len(food_results["foods"]) == 0:
        return None
    food_arr = []
    tracked_nutrients = []
    nutrient_nicknames = []
    for nutrient in nutrient_dict:
        if "nickname" in nutrient.keys():
            nutrient_nicknames.append(nutrient["nickname"])
        else:
            nutrient_nicknames.append(None)
        tracked_nutrients.append(nutrient["nutrientId"])
    food_results = food_results["foods"]
    # Remove extraneous pieces of data in the food description
    to_del = {'food':["finalFoodInputFoods", "dataType", "sources", "foodAttributes", "langual"], 
              'desc':["sd", "sn", "cn", "manu", "nf", "cf", "ff", "pf", "r", "rd", "ru", "ds"],
              }
    # Iterate through each food and remove extra information, and simplify names
    f = 0
    for food in food_results['foods']:
        for del_item in to_del["food"]:
            food.pop(del_item, None)
        for del_item in to_del["desc"]:
            food['foodAttributeTypes']['food_attributes'].pop(del_item, None)
        # sort nutrients by id if not already
        n_list = food["foodNutrients"]
        n_list.sort(key=operator.itemgetter("nutrientId"))
        # end sort
        n = 0
        for nutrient in food["foodNutrients"]:
            if n == len(tracked_nutrients):
                break
            # check if this is a nutrient we should record
            if nutrient["nutrientId"] == tracked_nutrients[n]:
                potential_name = nutrient_nicknames[n]
                if potential_name != None:
                    nutrient["nutrientName"] = potential_name
                n += 1
            # check if the food doesn't contain a tracked nutrient
            while n < len(tracked_nutrients) and nutrient["nutrientId"] > tracked_nutrients[n]:
                to_insert = nutrient_dict[n]
                to_insert.update(value=0)
                food["foodNutrients"].insert(n,to_insert)
                n += 1
        while n < len(tracked_nutrients) and food["foodNutrients"][-1]["nutrientId"] < tracked_nutrients[-1]:
            to_insert = nutrient_dict[n]
            to_insert.update(value=0)
            food["foodNutrients"].insert(n,to_insert)
            n += 1
        n = 0
        n_to_del = []
        for nutrient in food["foodNutrients"]:
            # check if this is a nutrient we should delete
            if nutrient["nutrientId"] not in tracked_nutrients:
                n_to_del.append(n)
            n += 1
        offset = 0
        for del_n in n_to_del:
            del food["foodNutrients"][del_n - offset]
            offset += 1
        # sort nutrients by id if not already
        n_list = food["foodNutrients"]
        n_list.sort(key=operator.itemgetter("nutrientId"))
        # end sort
        n = 0
        for nutrient in food["foodNutrients"]:
            if nutrient_nicknames[n] != None:
                food["foodNutrients"][n]["name"] = nutrient_nicknames[n] 
            nutrient["value"] = nutrient["value"] * (values[f]/100)
            n += 1
        f += 1
        food_arr.append(Food(food))
    return food_arr
