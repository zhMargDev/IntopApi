def find_category_by_id(categories, target_id):
    # Рекурсивная функция которая проходит по всем категориям и вложенннастям, и возвращает категорию по указанному id
    for category in categories:
        if category['id'] == target_id:
            return category
        if 'subcats' in category:
            result = find_category_by_id(category['subcats'], target_id)
            if result:
                return result
    return None