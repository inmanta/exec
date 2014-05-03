"""
    Copyright 2014 KU Leuven Research and Development - iMinds - Distrinet

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

    Administrative Contact: dnet-project-office@cs.kuleuven.be
    Technical Contact: bart.vanbrabant@cs.kuleuven.be
"""

from Imp.resources import Resource, resource, ResourceNotFoundExcpetion
from Imp.agent.handler import provider, ResourceHandler
from Imp.export import resource_to_id

import logging, os, shlex, subprocess

LOGGER = logging.getLogger(__name__)

@resource("exec::Run", agent = "host.name", id_attribute = "command")
class Run(Resource):
    """
        This class represents a service on a system.
    """
    fields = ("command", "creates", "cwd", "environment", "user", "group",
        "umask", "onlyif", "path", "reload", "reload_only", "returns", "timeout",
        "retries", "try_sleep", "unless")

@provider("exec::Run", name = "posix")
class PosixRun(ResourceHandler):
    """
        A handler to execute commands on posix compatible systems. This is 
        a very atypical resource as this executes a command. The check_resource
        method will determine based on the "reload_only", "creates", "unless" 
        and "onlyif" attributes if the command will be executed.
    """
    @classmethod
    def is_available(self, io):
        return io.file_exists("/bin/true")

    def _execute(self, command, timeout):
        args = shlex.split(command)

        if not os.path.exists(args[0]):
            return (-1, "", "", False)

        proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)

        try:
            outs, errs = proc.communicate(timeout=timeout)

            return (proc.returncode, outs, errs, False)
        except TimeoutExpired:
            proc.kill()
            outs, errs = proc.communicate()
            return (proc.returncode, outs, errs, True)

    def check_resource(self, resource):
        # a True for a condition means that the command may be executed.
        state = {"creates": True, "unless" : True, "onlyif" : True}

        if resource.creates is not None and resource.creates != "":
            # check if the file exists
            state["creates"] = not os.path.exists(resource.creates)

        if resource.unless is not None and resource.unless != "":
            # only execute this Run if this command fails

            # TODO: Log a warning is the command does not exist
            value = self._execute(resource.unless, resource.timeout)

            if value[0] == 0:
                state["unless"] = False

        if resource.onlyif is not None and resource.onlyif != "":
            # only execute this Run if this command is succesfull

            # TODO: Log a warning is the command does not exist
            value = self._execute(resource.onlyif, resource.timeout)

            if value[0] > 0:
                state["onlyif"] = False

        return state
            
    def list_changes(self, desired):
        return {}

    def can_reload(self):
        """
            Can this handler reload?
        """
        return True

    def do_cmd(self, resource, cmd):
        """
            Execute the command (or reload command) if required
        """
        state = self.check_resource(resource)

        run = True
        for k,v in state.items():
            run &= v

        if run:
            # TODO: add retry, user, group, umask, log,...
            LOGGER.info("Executing command")
            ret = self._execute(resource.command, resource.timeout)
            return True

        return False


    def do_reload(self, resource):
        """
            Reload this resource
        """
        if resource.reload:
            return self.do_cmd(resource, resource.reload)

        return self.do_cmd(resource, resource.command)

    def do_changes(self, resource):
        if resource.reload_only:
            # TODO It is only reload
            return False

        return self.do_cmd(resource, resource.command)

