import sys
import math
import time
import json
from pathlib import Path

import threading
import numpy as np
from datetime import timedelta as td
from typing import Dict, List, Tuple, Union, Any, Optional
from shapely.geometry import Point, Polygon, LineString

import pygame
import pygame_widgets as pw
from pygame_widgets.button import Button

import tkinter as tk
from tkinter import filedialog

from transcounter.utilities import IMAGES_DIR, initialize, LAST_USED_FILE_PATH

WIDTH, HEIGHT = 800, 600
WHITE = (150, 150, 150)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

MODES = ['car', 'truck', 'motorbike']


class Stopwatch:
    def __init__(self):
        self._start_time = None
        self._pause_time = None
        self._elapsed_time = 0
        self._paused = True
        self._stopped = True
        self._lock = threading.Lock()
        self._thread = None
        self._event = threading.Event()

    def start(self):
        with self._lock:
            if not self._stopped:
                return
            self._start_time = time.time() - self._elapsed_time
            self._paused = False
            self._stopped = False
            self._event.set()
            self._thread = threading.Thread(target=self._run)
            self._thread.daemon = True  # set as daemon so it exits when main thread exits
            self._thread.start()

    def pause(self):
        with self._lock:
            if self._paused or self._stopped:
                return
            self._elapsed_time = time.time() - self._start_time
            self._paused = True
            self._event.clear()

    def resume(self):
        with self._lock:
            if not self._paused or self._stopped:
                return
            self._start_time = time.time() - self._elapsed_time
            self._paused = False
            self._event.set()

    def stop(self):
        with self._lock:
            if self._stopped:
                return
            self._stopped = True
            self._elapsed_time = 0
            self._event.set()  # Set the event to exit the thread

    def reset(self):
        with self._lock:
            self.stop()

    def get_elapsed_time(self):
        with self._lock:
            if self._paused or self._stopped:
                return self._elapsed_time
            else:
                return time.time() - self._start_time

    def _run(self):
        while not self._stopped:
            self._event.wait()  # Wait for the event to be set
            if self._stopped:
                break
            time.sleep(0.1)  # Sleep for 0.1 seconds to avoid busy-waiting


def save_events(
        path: Union[str, Path],
        events_list: List[Dict[str, Any]]
):
    if not events_list:
        return

    p = Path(path)
    if p.suffix == '.json':
        with open(path, mode='w', encoding='utf-8') as f:
            json.dump(events_list, f)
    elif p.suffix == '.csv':
        headers = events_list[0].keys()
        with open(path, mode='w', encoding='utf-8') as f:
            f.write(';'.join(headers) + '\n')
            for event in events_list:
                f.write(
                    ';'.join(
                        str(v) if not isinstance(v, float)
                        else str(v).replace('.', ',')
                        for v in event.values()) + '\n'
                )
    else:
        raise ValueError(f'Unsupported file format: {p.suffix}')


def calculate_zone_polygons(
        canvas_width: int = 800,
        canvas_height: int = 600,
        side_coeff: float = 0.2,
        pad_x: int = 0,
        pad_y: int = 0
) -> Dict[int, List[Tuple[int, int]]]:
    side_height = canvas_height * side_coeff
    side_width = canvas_width * side_coeff
    canvas_coords = [
        (pad_x, pad_y),
        (pad_x, pad_y + canvas_height),
        (pad_x + canvas_width, pad_y + canvas_height),
        (pad_x + canvas_width, pad_y),
        (pad_x, pad_y)
    ]
    hole_coords = [
        (pad_x + side_width, pad_y + side_height),
        (pad_x + side_width, pad_y + canvas_height - side_height),
        (pad_x + canvas_width - side_width, pad_y + canvas_height - side_height),
        (pad_x + canvas_width - side_width, pad_y + side_height),
        (pad_x + side_width, pad_y + side_height)
    ]
    zone_polygons = {}
    for i in range(4):
        zone_polygons[i + 1] = canvas_coords[i:i+2] + hole_coords[i:i+2][::-1]
    return zone_polygons


def project_point_on_line(
        line_point1: Tuple[int, int],
        line_point2: Tuple[int, int],
        point: Tuple[int, int]
) -> Tuple[int, int]:
    # vector of the line
    line_vector = np.array(line_point2) - np.array(line_point1)

    # vector from the first point of the line to the point to be projected
    point_vector = np.array(point) - np.array(line_point1)

    projection = (
            np.array(line_point1) +
            np.dot(point_vector, line_vector) / np.dot(line_vector, line_vector) * line_vector
    )
    return projection


def calculate_normal_vector(
        point1: Tuple[int, int],
        point2: Tuple[int, int]
) -> Tuple[int, int]:
    """
    Calculate the normal vector of a line.

    Args:
        point1 (tuple): The first point of the line.
        point2 (tuple): The second point of the line.

    Returns:
        tuple: The normal vector of the line.
    """
    x1, y1 = point1
    x2, y2 = point2
    dx = x2 - x1
    dy = y2 - y1
    normal_x = -dy
    normal_y = dx
    length = math.sqrt(normal_x ** 2 + normal_y ** 2)
    normal_x /= length
    normal_y /= length
    return normal_x, normal_y


def parallel_offset(
        point1: Tuple[int, int],
        point2: Tuple[int, int],
        distance: Union[int, float]
):
    """
    Create a parallel offset of a line.

    Args:
        point1 (tuple): The first point of the line.
        point2 (tuple): The second point of the line.
        distance (float): The offset distance.

    Returns:
        tuple: The two points of the offset line.
    """
    normal_x, normal_y = calculate_normal_vector(point1=point1, point2=point2)
    offset_x = normal_x * distance
    offset_y = normal_y * distance
    offset_point1 = (point1[0] + offset_x, point1[1] + offset_y)
    offset_point2 = (point2[0] + offset_x, point2[1] + offset_y)
    return offset_point1, offset_point2


def distance_between_lines(
        line1_point1: Tuple[int, int],
        line1_point2: Tuple[int, int],
        line2_point1: Tuple[int, int],
        line2_point2: Tuple[int, int]
) -> int:
    # define direction vectors of the lines
    line1_direction = np.array(line1_point2) - np.array(line1_point1)
    # line2_direction = np.array(line2_point2) - np.array(line2_point1)

    # calculate the vector between a point on each line
    point_vector = np.array(line1_point1) - np.array(line2_point1)

    # calculate the cross product of the direction vectors and the vector between the points
    cross_product = line1_direction[0] * point_vector[1] - line1_direction[1] * point_vector[0]

    # if the lines are parallel, the cross product will be zero
    if cross_product == 0:
        # calculate distance between point and line
        numerator = np.abs(line1_direction[0] * point_vector[1] - line1_direction[1] * point_vector[0])
        denominator = np.linalg.norm(line1_direction)
        distance = numerator / denominator
    else:
        # calculate distance between lines
        numerator = np.abs(cross_product)
        denominator = np.linalg.norm(line1_direction)
        distance = numerator / denominator

    return round(distance)


def calculate_departure_area(
        zone_geometry: List[Tuple[int, int]],
        pad_coeff: Union[int, float] = 0.1,
        area_coeff: float = 2 / 3
) -> List[Tuple[int, int]]:
    # distance in the most wide part
    top_dist = distance_between_lines(
        zone_geometry[2], zone_geometry[3], zone_geometry[0], zone_geometry[1]
    )
    side_dist = math.dist(zone_geometry[2], zone_geometry[3]) * area_coeff
    left_offset = top_dist - top_dist * pad_coeff
    right_offset = top_dist * pad_coeff
    left_line = parallel_offset(zone_geometry[2], zone_geometry[3], -left_offset)
    right_line = parallel_offset(zone_geometry[2], zone_geometry[3], -right_offset)
    pre_bottom_line = left_line[0], right_line[0]
    top_offset = side_dist - side_dist * pad_coeff
    bottom_offset = side_dist * pad_coeff
    bottom_line = parallel_offset(pre_bottom_line[0], pre_bottom_line[1], -bottom_offset)
    top_line = parallel_offset(pre_bottom_line[0], pre_bottom_line[1], -top_offset)

    departure_area = convert_floats_to_ints([
        bottom_line[0], top_line[0], top_line[1], bottom_line[1]
    ])
    return departure_area


def calculate_mode_icons(
        dep_area_coords, modes: List[str], padding_fraction: float = 0.05
):
    width = math.dist(dep_area_coords[1], dep_area_coords[2])
    height = math.dist(dep_area_coords[0], dep_area_coords[1])
    padding = min(height, width) * padding_fraction
    left_segline = LineString(
        [dep_area_coords[0], dep_area_coords[1]]
    ).segmentize(height / len(modes))
    right_segline = LineString(
        [dep_area_coords[3], dep_area_coords[2]]
    ).segmentize(height / len(modes))

    zipcoords = list(zip(
            list(left_segline.coords), list(right_segline.coords)
    ))

    inner_rectangles = {}
    for i, mode in enumerate(modes):
        innercoords = [zipcoords[i][0], zipcoords[i + 1][0], zipcoords[i + 1][1], zipcoords[i][1]]
        pre_innerpoly = Polygon(innercoords)
        innerpoly = pre_innerpoly.buffer(-padding)
        polycoords = list(innerpoly.exterior.coords)[:-1]
        # left top width height
        x1, y1 = polycoords[0]
        x2, y2 = polycoords[2]
        polydata = [min(x1, x2), min(y1, y2), abs(x2-x1), abs(y2-y1)]
        inner_rectangles[mode] = polydata

    return inner_rectangles


def convert_floats_to_ints(
        tuple_list: List[Tuple[Union[int, float], Union[int, float]]]
) -> List[Tuple[int, int]]:
    return [
        (int(t[0]), int(t[1])) for t in tuple_list
    ]

def undo_event(
        events_list: List[Dict[str, Any]],
        event_count: Dict[str, int]
):
    if events_list:
        last_event = events_list.pop()
        text_event = f"{last_event['mode']}, {last_event['from']} > {last_event['to']}"
        if text_event in event_count and event_count[text_event] != 0:
            event_count[text_event] -= 1


def create_file_gui(
        start_directory: Optional[Union[Path, str]]
) -> Optional[str]:
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[
            ("CSV Files", "*.csv"),
            ("JSON Files", "*.json")
        ],
        title="File name to create",
        initialdir=start_directory,
        initialfile='transcounter'
    )
    root.destroy()
    if file_path:
        with open(LAST_USED_FILE_PATH, 'w') as f:
            f.write(file_path)
    return file_path


def main_gui(
        events_path: Union[Path, str]
):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    screen.set_alpha(0)

    icons = {
        mode: pygame.transform.scale(
            pygame.image.load(Path(IMAGES_DIR / f'{mode}.png').resolve()).convert_alpha(), (50, 50)
        )
        for mode in MODES
    }

    zones_coords = calculate_zone_polygons(
        canvas_width=WIDTH - 150,
        canvas_height=HEIGHT,
        pad_x=150
    )
    departure_areas_coords = {
        k: calculate_departure_area(v) for k, v in zones_coords.items()
    }
    departure_areas_objects = {
        k: Polygon(v) for k, v in departure_areas_coords.items()
    }
    mode_icons_coords = {
        k: calculate_mode_icons(v, modes=list(icons.keys())) for k, v in departure_areas_coords.items()
    }
    zones_objects = {
        k: Polygon(v) for k, v in zones_coords.items()
    }
    mode_icons_rects = {
        orig_zone: {k: pygame.Rect(*v) for k, v in icons_dict.items()} for orig_zone, icons_dict in mode_icons_coords.items()
    }

    pygame.display.set_caption('Flow counting')
    font = pygame.font.Font(None, 20)

    clock = pygame.time.Clock()

    dragging = None
    offset_x = 0
    offset_y = 0

    event_count = {}
    event_list = []

    sw = Stopwatch()
    timer_starter = Button(
        screen, 10, 10, 35, 35,
        onClick=sw.start,
        text='Start',
        shadowDistance=1,
        fontSize=10
    )
    timer_suspender = Button(
        screen, 55, 10, 35, 35,
        onClick=sw.pause,
        text='Pause',
        shadowDistance=1,
        fontSize=10
    )
    timer_resumer = Button(
        screen, 100, 10, 35, 35,
        onClick=sw.resume,
        text='Resume',
        shadowDistance=1,
        fontSize=10
    )
    action_undo = Button(
        screen, 10, screen.get_height() - 45, 35, 35,
        onClick=lambda: undo_event(event_list, event_count),
        text='Undo',
        shadowDistance=1,
        fontSize=10
    )
    prev_width = screen.get_width()
    prev_height = screen.get_height()

    # Game loop
    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for orig_zone, icons_dict in mode_icons_rects.items():
                    for icon_mode, icon_rect in icons_dict.items():
                        if icon_rect.collidepoint(event.pos):
                            dragging = (orig_zone, icon_mode)
                            offset_x = icon_rect.x - event.pos[0]
                            offset_y = icon_rect.y - event.pos[1]
                            break
            elif event.type == pygame.MOUSEBUTTONUP:
                if dragging:
                    pt = Point(pygame.mouse.get_pos())
                    orig_zone, mode = dragging
                    for zone_name, zone_poly in zones_objects.items():
                        if zone_poly.contains(pt):
                            if departure_areas_objects[orig_zone].contains(pt):
                                print('Own zone is not permitted!')
                                break
                            key = f"{mode}, {orig_zone} > {zone_name}"
                            if key in event_count:
                                event_count[key] += 1
                            else:
                                event_count[key] = 1
                            event_list.append({
                                'mode': mode,
                                'from': orig_zone,
                                'to': zone_name,
                                'time': sw.get_elapsed_time()
                            })
                            save_events(events_path, event_list)
                            break
                    mode_icons_rects[orig_zone][mode].x = mode_icons_coords[orig_zone][mode][0]
                    mode_icons_rects[orig_zone][mode].y = mode_icons_coords[orig_zone][mode][1]
                    dragging = None
            elif event.type == pygame.MOUSEMOTION and dragging is not None:
                orig_zone, mode = dragging
                mode_icons_rects[orig_zone][mode].x = event.pos[0] + offset_x
                mode_icons_rects[orig_zone][mode].y = event.pos[1] + offset_y
            elif event.type == pygame.VIDEORESIZE:
                zones_coords = calculate_zone_polygons(
                    canvas_width=event.w - 150,
                    canvas_height=event.h,
                    pad_x=150
                )
                departure_areas_coords = {
                    k: calculate_departure_area(v) for k, v in zones_coords.items()
                }
                departure_areas_objects = {
                    k: Polygon(v) for k, v in departure_areas_coords.items()
                }
                mode_icons_coords = {
                    k: calculate_mode_icons(v, modes=list(icons.keys()))
                    for k, v in departure_areas_coords.items()
                }
                zones_objects = {
                    k: Polygon(v) for k, v in zones_coords.items()
                }
                mode_icons_rects = {
                    orig_zone: {k: pygame.Rect(*v) for k, v in icons_dict.items()}
                    for orig_zone, icons_dict in mode_icons_coords.items()
                }
                height_change = screen.get_height() - prev_height
                action_undo.moveY(height_change)
                prev_height = screen.get_height()
                prev_width = screen.get_width()

                # Draw everything
        screen.fill(WHITE)

        for orig_zone, icons_dict in mode_icons_rects.items():
            for icon_mode, icon_rect in icons_dict.items():
                screen.blit(icons[icon_mode], (icon_rect.center[0] - 25, icon_rect.center[1] - 25))
                pygame.draw.rect(screen, BLACK, icon_rect, width=1)

        zones = {
            k: pygame.draw.polygon(
                surface=screen,
                points=v,
                color=BLACK,
                width=5
            ) for k, v in zones_coords.items()
        }
        departure_areas = {
            k: pygame.draw.polygon(
                surface=screen,
                points=v,
                color=BLACK,
                width=2
            ) for k, v in departure_areas_coords.items()
        }

        y = 55
        timer = font.render("Time: " + str(td(seconds=round(sw.get_elapsed_time()))), True, BLACK)
        screen.blit(timer, (10, y))
        y += 20
        header = font.render("Events", True, WHITE, (0, 0, 0))
        screen.blit(header, (10, y))
        events_counter = font.render(f"{len(event_list)}", True, BLACK)
        screen.blit(events_counter, (80, y))
        y += 40
        for key, value in event_count.items():
            text = font.render(f"{key}: {value}", True, (0, 0, 0))
            screen.blit(text, (10, y))
            y += 20

        pw.update(events)
        pygame.display.flip()
        clock.tick(60)


def main(
        args_list: Optional[List[str]] = None  # unused here for now
):
    last_used_path = initialize()
    last_used_path_parent = None if not last_used_path else last_used_path.parent
    events_path = create_file_gui(
        start_directory=last_used_path_parent
    )
    if events_path:
        main_gui(events_path=events_path)


if __name__ == '__main__':
    main()
