
def group_sequences(item_list, are_in_sequence):

    def group(ranges, current):
        if len(ranges) == 0:
            ranges.append([current])
        else:
            last_range = ranges[-1]
            last_item = last_range[-1]
            if are_in_sequence(last_item, current):
                last_range.append(current)
            else:
                ranges.append([current])

        return ranges

    return reduce(group, item_list, [])
