# Keypirinha launcher (keypirinha.com)
import re
import os
import keypirinha as kp
import keypirinha_util as kpu
import keypirinha_net as kpnet
from todoist.api import TodoistAPI

class Todoist(kp.Plugin):

    DEFAULT_ADD_TASK_LABEL = "atodoist"
    DEFAULT_LIST_ALL_TASKS = "todoist"
    DEFAULT_PROJECT_NAME = "Inbox"

    ITEMCAT_ADD = kp.ItemCategory.USER_BASE + 1
    ITEMCAT_LIST = kp.ItemCategory.USER_BASE + 2

    ACTION_COMPLETE_TASK = "complete_task"
    ACTION_DELETE_TASK = "delete_task"

    def __init__(self):
        super().__init__()

    def _read_config(self):

        settings = self.load_settings()
        self.add_task_label = settings.get_stripped("add_task_label", "main", self.DEFAULT_ADD_TASK_LABEL)
        self.list_tasks_label = settings.get_stripped("list_tasks_label", "main", self.DEFAULT_LIST_ALL_TASKS)
        self.user_token = settings.get_stripped("user_token", "main", "")
        self.project_name = settings.get_stripped("project_name", "main", self.DEFAULT_PROJECT_NAME)

        self.api = TodoistAPI(self.user_token)
        self.api.sync()
        self.project = next((p for p in self.api.state['projects'] if p.data["name"] == self.project_name), None)
        self.project_id = self.project.data["id"]
        self.items = [item for item in self.api.state['items'] if item.data['project_id'] == self.project_id and 'checked' in item.data and item.data['checked'] == 0]

    def _sync(self):
        self.api.sync()
        self.project = next((p for p in self.api.state['projects'] if p.data["name"] == self.project_name), None)
        self.project_id = self.project.data["id"]
        self.items = [item for item in self.api.state['items'] if item.data['project_id'] == self.project_id and 'checked' in item.data and item.data['checked'] == 0]

    def on_start(self):
        self.dbg("On Start")
        self._read_config()

        # register actions
        actions = [
            self.create_action(
                name=self.ACTION_COMPLETE_TASK,
                label="Complete your task",
                short_desc="Complete your task"),
            self.create_action(
                name=self.ACTION_DELETE_TASK,
                label="Delete your task",
                short_desc="Delete your task")
        ]
        self.set_actions(self.ITEMCAT_LIST, actions)

    def on_catalog(self):
        self.set_catalog([
            self.create_item(
                category=self.ITEMCAT_LIST,
                label=self.list_tasks_label,
                short_desc="Your To-Do List",
                target=self.list_tasks_label,
                args_hint=kp.ItemArgsHint.REQUIRED,
                hit_hint=kp.ItemHitHint.NOARGS
            ),
            self.create_item(
                category=self.ITEMCAT_ADD,
                label=self.add_task_label,
                short_desc="Add To-Do List",
                target=self.list_tasks_label,
                args_hint=kp.ItemArgsHint.REQUIRED,
                hit_hint=kp.ItemHitHint.NOARGS
            ),
        ])

    def on_suggest(self, user_input, items_chain):
        suggestions = []
        match = kp.Match.FUZZY
        if len(items_chain) > 0:
            if items_chain[0].category() == self.ITEMCAT_LIST:
                self._sync()
                for item in self.items:
                    suggestions.append(self.create_item(
                        category=self.ITEMCAT_LIST,
                        label=item.data['content'],
                        short_desc=item.data['content'],
                        target=str(item.data['id']),
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.IGNORE,
                    ))
            elif items_chain[0].category() == self.ITEMCAT_ADD:
                match = kp.Match.ANY
                suggestions.append(self.create_item(
                    category=self.ITEMCAT_ADD,
                    label="Add Task",
                    short_desc=user_input,
                    target=str(self.project_id),
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE,
                ))

        self.set_suggestions(suggestions, match, kp.Sort.NONE)

    def on_execute(self, item, action):
        target = int(item.target())
        if item.category() == self.ITEMCAT_ADD and item.short_desc() != None:
            item = self.api.items.add(item.short_desc(), project_id=target)
            self.api.commit()
        else:
            if action == self.ACTION_COMPLETE_TASK:
                item = self.api.items.get_by_id(target)
                item.complete()
                self.api.commit()
            elif action == self.ACTION_DELETE_TASK:
                item = self.api.items.get_by_id(target)
                item.delete()
                self.api.commit()
            else:
                item = self.api.items.get_by_id(target)
                item.complete()
                self.api.commit()

    def on_activated(self):
        pass

    def on_deactivated(self):
        pass

    def on_events(self, flags):
        if flags & kp.Events.PACKCONFIG:
            self.on_start()
