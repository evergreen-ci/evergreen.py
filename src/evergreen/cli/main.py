from __future__ import absolute_import

from enum import Enum
import json
import yaml

import click

from evergreen.api import EvergreenApi


DisplayFormat = Enum('DisplayFormat', 'human json yaml')


def fmt_output(fmt, data):
    """
    Convert the given data into the specified format.

    :param fmt: DisplayFormat to use.
    :param data: Data to convertn.
    :return: Data is specified format.
    """
    if fmt == DisplayFormat.json:
        return json.dumps(data, indent=4)
    if fmt == DisplayFormat.yaml:
        return yaml.safe_dump(data)
    return data


@click.group()
@click.option('--json', 'display_format', flag_value=DisplayFormat.json,
              help='Write output in json.')
@click.option('--yaml', 'display_format', flag_value=DisplayFormat.yaml,
              help='Write output in yaml.')
@click.option('--human-readable', 'display_format', flag_value=DisplayFormat.human, default=True,
              help='Write output in a human readable format.')
@click.pass_context
def cli(ctx, display_format):
    ctx.ensure_object(dict)
    ctx.obj['api'] = EvergreenApi.get_api(use_config_file=True)
    ctx.obj['format'] = display_format


@cli.command()
@click.pass_context
def list_hosts(ctx):
    api = ctx.obj['api']
    fmt = ctx.obj['format']
    host_list = api.all_hosts()
    click.echo(fmt_output(fmt, [host.json for host in host_list]))


@cli.command()
@click.pass_context
@click.option('-p', '--project', required=True)
@click.option('-l', '--limit', type=int)
def list_patches(ctx, project, limit):
    api = ctx.obj['api']
    fmt = ctx.obj['format']
    patches = []
    for i, p in enumerate(api.patches_by_project(project)):
        patches.append(p.json)
        if limit and i > limit:
            break
    click.echo(fmt_output(fmt, patches))


@cli.command()
@click.pass_context
def list_projects(ctx):
    api = ctx.obj['api']
    fmt = ctx.obj['format']
    project_list = api.all_projects()
    projects = [project.json for project in project_list]
    click.echo(fmt_output(fmt, projects))


@cli.command()
@click.pass_context
@click.option('-a', '--after-date', required=True)
@click.option('-b', '--before-date', required=True)
@click.option('-p', '--project', required=True)
@click.option('-d', '--distros', multiple=True)
@click.option('--group-by')
@click.option('-g', '--group-num-days')
@click.option('-r', '--requesters', multiple=True)
@click.option('-s', '--sort')
@click.option('--tests', multiple=True)
@click.option('-t', '--tasks', multiple=True)
@click.option('-v', '--variants', multiple=True)
def test_stats(ctx, after_date, before_date, project, distros, group_by, group_num_days, requesters,
               sort, tests, tasks, variants):
    api = ctx.obj['api']
    fmt = ctx.obj['format']

    test_stat_list = api.test_stats_by_project(project, after_date, before_date, group_num_days,
                                               requesters, tests, tasks, variants, distros,
                                               group_by, sort)
    test_stats = [t.json for t in test_stat_list]
    click.echo(fmt_output(fmt, test_stats))


def main():
    return cli(obj={})
