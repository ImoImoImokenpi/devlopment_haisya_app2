from itertools import combinations
from collections import defaultdict
from ..models import Entry  # パスは適宜調整
import random

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


def hard_constraints_ok(entry_a, entry_b):
    """
    絶対に守るべき制約を確認する。
    False なら同乗不可。
    - NGペア (avoid_with)
    - リハーサル有無の不一致
    - スケジュール（両者に schedule_id がある場合は一致必須）
    - 早帰り有無の不一致
    """
    if is_ng_pair(entry_a, entry_b):
        return False
    if entry_a.has_rehersal != entry_b.has_rehersal:
        return False
    if (entry_a.schedule_id and entry_b.schedule_id
            and entry_a.schedule_id != entry_b.schedule_id):
        return False
    if entry_a.early_leave != entry_b.early_leave:
        return False
    return True


def calculate_soft_score(entry_a, entry_b):
    """
    ジャンル・年齢のみのソフトスコア。
    ランダム／ドキドキでは高低を操作する対象。
    """
    score = 0
    if (entry_a.user.genre and entry_b.user.genre
            and entry_a.user.genre == entry_b.user.genre):
        score += 30
    if entry_a.user.age and entry_b.user.age:
        if abs(entry_a.user.age - entry_b.user.age) <= 1:
            score += 30
    return score


def calculate_pair_score(entry_a, entry_b):
    """
    ペアのスコアを返す。高いほど同乗させたい。
    NG ペアは -999999。
    """
    if is_ng_pair(entry_a, entry_b):
        return -999999

    score = 0

    if entry_a.early_leave and entry_b.early_leave:
        score += 300

    if entry_a.has_rehersal == entry_b.has_rehersal:
        score += 100

    if (entry_a.schedule_id
            and entry_b.schedule_id
            and entry_a.schedule_id == entry_b.schedule_id):
        score += 50

    score += calculate_soft_score(entry_a, entry_b)

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


def _valid_cars_for(passenger, cars):
    """ハード制約をすべて満たす空き車を返す。"""
    result = []
    for car in cars:
        if len(car["members"]) >= car["capacity"]:
            continue
        if all(hard_constraints_ok(passenger, m) for m in car["members"]):
            result.append(car)
    return result


def assign_to_cars_random(room_id):
    """ハード制約を守りつつランダムに割り当てる。"""
    entries = Entry.query.filter_by(room_id=room_id).all()

    if not entries:
        return [], []

    cars = build_cars_from_entries(entries)

    if not cars:
        return [], entries

    driver_ids = {car["driver_entry"].id for car in cars}
    passengers = [e for e in entries if e.id not in driver_ids]

    # ハード制約で絞り込みやすい人を先に割り当て
    sorted_passengers = sorted(
        passengers,
        key=lambda e: (e.schedule_id is not None, e.has_rehersal),
        reverse=True,
    )

    unassigned = []
    for passenger in sorted_passengers:
        available = _valid_cars_for(passenger, cars)
        if available:
            random.choice(available)["members"].append(passenger)
        else:
            unassigned.append(passenger)

    return cars, unassigned


def assign_to_cars_dokidoki(room_id):
    """ハード制約を守りつつソフトスコア（ジャンル・年代）が最も低い車を選ぶ。"""
    entries = Entry.query.filter_by(room_id=room_id).all()

    if not entries:
        return [], []

    cars = build_cars_from_entries(entries)

    if not cars:
        return [], entries

    driver_ids = {car["driver_entry"].id for car in cars}
    passengers = [e for e in entries if e.id not in driver_ids]

    sorted_passengers = sorted(
        passengers,
        key=lambda e: (e.schedule_id is not None, e.has_rehersal),
        reverse=True,
    )

    def worst_soft_car(passenger):
        """ハード制約OK の車の中でソフトスコアが最も低い車を返す。"""
        available = _valid_cars_for(passenger, cars)
        if not available:
            return None
        def avg_soft(car):
            scores = [calculate_soft_score(passenger, m) for m in car["members"]]
            return sum(scores) / len(scores) if scores else 0
        return min(available, key=avg_soft)

    unassigned = []
    for passenger in sorted_passengers:
        car = worst_soft_car(passenger)
        if car:
            car["members"].append(passenger)
        else:
            unassigned.append(passenger)

    return cars, unassigned
