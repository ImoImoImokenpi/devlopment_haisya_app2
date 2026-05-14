# rooms/matching.py

from itertools import combinations
from collections import defaultdict
from ..models import Entry  # パスは適宜調整


def build_cars_from_entries(entries):
    """
    has_car=True のエントリから「車リスト」を生成する。
    戻り値: [{"driver_entry": Entry, "capacity": int, "members": []}]
    """
    cars = []
    for entry in entries:
        if entry.has_car and entry.capacity and entry.capacity > 0:
            cars.append({
                "driver_entry": entry,
                "capacity": entry.capacity + 1,
                "members": [entry],  # ドライバー自身を最初に追加
            })
    return cars


def parse_avoid_list(avoid_with_str):
    """
    avoid_with は「田中,佐藤」のようなカンマ区切り想定。
    → set で返す（空文字・None は空set）
    """
    if not avoid_with_str:
        return set()
    return {name.strip() for name in avoid_with_str.split(",") if name.strip()}


def is_ng_pair(entry_a, entry_b):
    """
    どちらかが相手の名前を avoid_with に書いていたら NG。
    User.name で照合する。
    """
    a_avoids = parse_avoid_list(entry_a.avoid_with)
    b_avoids = parse_avoid_list(entry_b.avoid_with)

    a_name = entry_a.user.username  # User モデルに name があると仮定
    b_name = entry_b.user.username

    return b_name in a_avoids or a_name in b_avoids


def calculate_pair_score(entry_a, entry_b):
    """
    ペアのスコアを返す。高いほど同乗させたい。
    NG ペアは -999999。
    """
    # ハード制約（即除外）
    if is_ng_pair(entry_a, entry_b):
        return -999999

    score = 0

    # 早帰り同士を最優先でまとめる ← 追加
    if entry_a.early_leave and entry_b.early_leave:
        score += 300

    # リハの合致：両者 has_rehersal が同じ（True同士 or False同士）
    if entry_a.has_rehersal == entry_b.has_rehersal:
        score += 100

    # 出演順の合致：schedule_id が同じ（None同士は合致扱いしない）
    if (entry_a.schedule_id
            and entry_b.schedule_id
            and entry_a.schedule_id == entry_b.schedule_id):
        score += 50
    
    # 同じジャンル同士を優先（None同士は合致扱いしない）
    if (entry_a.user.genre
            and entry_b.user.genre
            and entry_a.user.genre == entry_b.user.genre):
        score += 30
    
    # 年齢が近いほど高スコア（差が5歳以内なら加点）
    if entry_a.user.age and entry_b.user.age:
        age_diff = abs(entry_a.user.age - entry_b.user.age)
        if age_diff <= 1:
            score += 30

    return score


def assign_to_cars(room_id):
    """
    room_id に紐づく Entry を取得し、車への割り当てを行う。

    戻り値:
        List[dict]  ← [{"driver_entry": Entry, "capacity": int, "members": [Entry, ...]}, ...]
        unassigned: List[Entry]  ← どの車にも入れなかった人
    """
    entries = Entry.query.filter_by(room_id=room_id).all()

    if not entries:
        return [], []

    cars = build_cars_from_entries(entries)

    if not cars:
        # 車を持っている人がいない
        return [], entries

    # 乗客候補（ドライバーを除く）
    driver_ids = {car["driver_entry"].id for car in cars}
    passengers = [e for e in entries if e.id not in driver_ids]

    # 全ペア（乗客×車ドライバーも含めてスコアを計算する必要はなく
    # 乗客同士のスコアで「誰と同じ車か」を決める）
    # → 各乗客について「どの車（ドライバー）と相性が良いか」を計算
    assignments = {car["driver_entry"].id: car for car in cars}

    def car_has_room(car):
        return len(car["members"]) < car["capacity"]

    def best_car_for(passenger):
        """
        乗客にとって最もスコアが高い（かつ空きがある）車を返す。
        車内の既乗員全員との平均スコアで評価する。
        """
        best_score = -999999
        best_car = None
        for car in cars:
            if not car_has_room(car):
                continue
            # この車に乗っている全員との相性チェック
            scores = []
            ng = False
            for member in car["members"]:
                s = calculate_pair_score(passenger, member)
                if s == -999999:
                    ng = True
                    break
                scores.append(s)
            if ng:
                continue
            avg = sum(scores) / len(scores) if scores else 0
            if avg > best_score:
                best_score = avg
                best_car = car
        return best_car

    # 乗客をスコアが取りやすい順（schedule_id あり優先）でソートして割り当て
    sorted_passengers = sorted(
        passengers,
        key=lambda e: (
            e.schedule_id is not None,   # schedule_id ありを先に
            e.has_rehersal,              # リハありを先に
        ),
        reverse=True,
    )

    unassigned = []
    for passenger in sorted_passengers:
        car = best_car_for(passenger)
        if car:
            car["members"].append(passenger)
        else:
            unassigned.append(passenger)

    return cars, unassigned