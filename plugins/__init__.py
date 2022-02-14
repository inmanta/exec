"""
    Copyright 2018 Inmanta

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

    Contact: code@inmanta.com
"""

import shlex
import subprocess

from inmanta.agent import handler
from inmanta.plugins import plugin
from inmanta.resources import Resource, resource


@plugin
def in_shell(command: "string"):
    """Wrap the command such that it is executed in a shell"""
    return subprocess.list2cmdline(["sh", "-c", command])


@resource("exec::Run", agent="host.name", id_attribute="command")
class Run(Resource):
    """
    This class represents a service on a system.
    """

    fields = (
        "command",
        "creates",
        "cwd",
        "environment",
        "onlyif",
        "path",
        "reload",
        "reload_only",
        "returns",
        "timeout",
        "unless",
        "skip_on_fail",
    )


@handler.provider("exec::Run", name="posix")
class PosixRun(handler.ResourceHandler):
    """
    A handler to execute commands on posix compatible systems. This is
    a very atypical resource as this executes a command. The check_resource
    method will determine based on the "reload_only", "creates", "unless"
    and "onlyif" attributes if the command will be executed.
    """

    def available(self, resource):
        return self._io.file_exists("/bin/true")

    def _execute(self, command, timeout, cwd=None, env={}):
        args = shlex.split(command)
        if env is None or len(env) == 0:
            env = None
        return self._io.run(args[0], args[1:], env, cwd, timeout=timeout)

    def check_resource(self, ctx, resource):
        return resource

    def list_changes(self, ctx, resource):
        # a True for a condition means that the command may be executed.
        execute = True

        if resource.creates is not None and resource.creates != "":
            # check if the file exists
            execute &= not self._io.file_exists(resource.creates)

        if resource.unless is not None and resource.unless != "":
            # only execute this Run if this command fails
            value = self._execute(
                resource.unless, resource.timeout, env=resource.environment
            )
            ctx.info(
                "Unless cmd %(cmd)s: out: '%(stdout)s', err: '%(stderr)s', returncode: %(retcode)s",
                cmd=resource.unless,
                stdout=value[0],
                stderr=value[1],
                retcode=value[2],
            )

            execute &= value[2] != 0

        if resource.onlyif is not None and resource.onlyif != "":
            # only execute this Run if this command is succesfull
            value = self._execute(
                resource.onlyif, resource.timeout, env=resource.environment
            )
            ctx.info(
                "Onlyif cmd %(cmd)s: out: '%(stdout)s', err: '%(stderr)s', returncode: %(retcode)s",
                cmd=resource.onlyif,
                stdout=value[0],
                stderr=value[1],
                retcode=value[2],
            )

            execute &= value[2] == 0

        ctx.set("execute", execute)
        return {}

    def can_reload(self):
        """
        Can this handler reload?
        """
        return True

    def do_cmd(self, ctx, resource, cmd):
        """
        Execute the command (or reload command) if required
        """
        if ctx.get("execute"):
            cwd = None
            if resource.cwd != "":
                cwd = resource.cwd
            ctx.debug(
                "Execute %(cmd)s with timeout %(timeout)s and working dir %(cwd)s and env %(env)s",
                cmd=cmd,
                timeout=resource.timeout,
                cwd=cwd,
                env=resource.environment,
            )
            ret = self._execute(
                cmd, resource.timeout, cwd=cwd, env=resource.environment
            )
            if ret[2] not in resource.returns:
                ctx.error(
                    "Failed to execute %(cmd)s: out: '%(stdout)s', err: '%(stderr)s', returncode: %(retcode)s ",
                    cmd=cmd,
                    stdout=ret[0],
                    stderr=ret[1],
                    retcode=ret[2],
                )

                if resource.skip_on_fail:
                    raise handler.SkipResource("Failed to execute command: %s" % ret[1])
                else:
                    raise Exception("Failed to execute command: %s" % ret[1])
            else:
                ctx.info(
                    "Executed %(cmd)s: out: '%(stdout)s', err: '%(stderr)s', returncode: %(retcode)s ",
                    cmd=cmd,
                    stdout=ret[0],
                    stderr=ret[1],
                    retcode=ret[2],
                )
            return True

        return False

    def do_reload(self, ctx, resource):
        """
        Reload this resource
        """
        if resource.reload:
            return self.do_cmd(ctx, resource, resource.reload)

        return self.do_cmd(ctx, resource, resource.command)

    def do_changes(self, ctx, resource, changes):
        if resource.reload_only:
            # TODO It is only reload
            return

        if self.do_cmd(ctx, resource, resource.command):
            ctx.set_updated()
