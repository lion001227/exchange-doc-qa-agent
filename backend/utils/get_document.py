def has_document(tool_list:list):
    for tool in tool_list:
        if tool in ["sse_latest_announcements","szse_latest_announcements"]:
            return False
    return True