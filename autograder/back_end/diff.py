from typing import List, Tuple, Dict

# Consumes two strings.
# Produces a list of tuple of (left_start, right_start, len).
# For non-matching blocks, one of the starting positions will be -1.
# (The offset parameters are only used internally during recursion.)
def diff(left:str, right:str, min_match_len:int=7, left_offset:int=0, right_offset:int=0) -> List[Tuple[int,int,int]]:
    # Check the easy solution
    if left == right:
        return [(left_offset, right_offset, len(left))]

    # Make a left and right mapping of all blocks of size min_match_len to a list of starting locations. (We use a list capped at size two so we can tell which matches are unique)
    l_map:Dict[str,List[int]] = {}
    for i in range(len(left) + 1 - min_match_len):
        s = left[i : i + min_match_len]
        if s in l_map:
            if len(l_map[s]) < 2:
                l_map[s].append(i)
        else:
            l_map[s] = [i]
    r_map:Dict[str,List[int]] = {}
    for i in range(len(right) + 1 - min_match_len):
        s = right[i : i + min_match_len]
        if s in r_map:
            if len(r_map[s]) < 2:
                r_map[s].append(i)
        else:
            r_map[s] = [i]

    # Find unique (one-to-one) matches
    unique_matches:List[Tuple[int,int,int]] = []
    for s in l_map:
        if not s in r_map:
            continue
        if len(l_map[s]) != 1:
            continue
        if len(r_map[s]) != 1:
            continue
        l_start = l_map[s][0]
        r_start = r_map[s][0]
        if len(unique_matches) == 0 or l_start >= unique_matches[-1][0] + unique_matches[-1][2] or l_start < unique_matches[-1][0]: # If it's not inside the same block as the last match
            l_end = l_start + min_match_len
            r_end = r_start + min_match_len
            while l_start > 0 and r_start > 0 and left[l_start - 1] == right[r_start - 1]:
                l_start -= 1
                r_start -= 1
            while l_end < len(left) and r_end < len(right) and left[l_end] == right[r_end]:
                l_end += 1
                r_end += 1
            unique_matches.append((l_start, r_start, l_end - l_start))

    # Find the biggest unique match
    best_match = -1
    for i in range(len(unique_matches)):
        if best_match < 0 or unique_matches[i][2] > unique_matches[best_match][2]:
            best_match = i

    # We got a unique match, so let's recurse
    if best_match >= 0:
        match = unique_matches[best_match]
        del unique_matches
        del l_map
        del r_map
        bef = diff(left[:match[0]], right[:match[1]], min_match_len, left_offset, right_offset)
        aft = diff(left[match[0] + match[2]:], right[match[1] + match[2]:], min_match_len, left_offset + match[0] + match[2], right_offset + match[1] + match[2])
        adjusted_match = (match[0] + left_offset, match[1] + right_offset, match[2]);
        return bef + [adjusted_match] + aft
    del unique_matches

    # Try first matches
    first_matches:List[Tuple[int,int,int]] = []
    for s in l_map:
        if not s in r_map:
            continue
        l_start = l_map[s][0]
        r_start = r_map[s][0]
        if len(first_matches) == 0 or l_start >= first_matches[-1][0] + first_matches[-1][2] or l_start < first_matches[-1][0]: # If it's not inside the same block as the last match
            l_end = l_start + min_match_len
            r_end = r_start + min_match_len
            while l_start > 0 and r_start > 0 and left[l_start - 1] == right[r_start - 1]:
                l_start -= 1
                r_start -= 1
            while l_end < len(left) and r_end < len(right) and left[l_end] == right[r_end]:
                l_end += 1
                r_end += 1
            first_matches.append((l_start, r_start, l_end - l_start))

    # Find the biggest first match
    best_match = -1
    for i in range(len(first_matches)):
        if best_match < 0 or first_matches[i][2] > first_matches[best_match][2]:
            best_match = i

    # We got a match, so let's recurse
    if best_match >= 0:
        match = first_matches[best_match]
        del first_matches
        del l_map
        del r_map
        bef = diff(left[:match[0]], right[:match[1]], min_match_len, left_offset, right_offset)
        aft = diff(left[match[0] + match[2]:], right[match[1] + match[2]:], min_match_len, left_offset + match[0] + match[2], right_offset + match[1] + match[2])
        adjusted_match = (match[0] + left_offset, match[1] + right_offset, match[2])
        return bef + [adjusted_match] + aft

    # No matches, so just return the two parts as mismatches
    results:List[Tuple[int,int,int]] = []
    if len(left) > 0:
        results.append((left_offset, -1, len(left)))
    if len(right) > 0:
        results.append((-1, right_offset, len(right)))
    return results

def str_dist(a:str, b:str, min_match_len:int=2) -> int:
    left = 0
    right = 0
    eq = 0
    for ls, rs, ln in diff(a, b, min_match_len):
        if ls >= 0 and rs >= 0:
            eq += ln
        elif ls >= 0:
            left += ln
        else:
            right += ln
    return 5 * (left + right) - eq

if __name__ == '__main__':
    left = 'alligator baboon cat dog elephant frog'
    right = 'ant baboon caribou dog frog giraffe'
    results = diff(left, right, 3)
    for res in results:
        if res[0] >= 0 and res[1] >= 0:
            print(f'=== "{left[res[0]:res[0] + res[2]]}"')
        elif res[0] >= 0:
            print(f'<<< "{left[res[0]:res[0] + res[2]]}"')
        else:
            print(f'>>> "{right[res[1]:res[1] + res[2]]}"')
