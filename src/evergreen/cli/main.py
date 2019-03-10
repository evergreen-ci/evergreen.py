from __future__ import absolute_import

import click

from evergreen.api import EvergreenApi

project_id = 'mongodb-mongo-master'


@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)
    ctx.obj['api'] = EvergreenApi.get_api(use_config_file=True)


@cli.command()
@click.pass_context
def list_hosts(ctx):
    api = ctx.obj['api']
    host_list = api.get_all_hosts()
    for host in host_list:
        click.echo(host)


@cli.command()
@click.pass_context
@click.option('-p', '--project', required=True)
@click.option('-l', '--limit', type=int)
def list_patches(ctx, project, limit):
    api = ctx.obj['api']
    for i, p in enumerate(api.patches_by_project(project)):
        click.echo(p)
        if limit and i > limit:
            break


@cli.command()
@click.pass_context
def list_projects(ctx):
    api = ctx.obj['api']
    project_list = api.get_all_projects()
    click.echo('Project ID:\tProject Name')
    click.echo('-----------\t------------')
    for project in project_list:
        click.echo('{}: {}'.format(project.identifier, project.display_name))


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

    test_stat_list = api.test_stats_by_project(project, after_date, before_date, group_num_days,
                                               requesters, tests, tasks, variants, distros,
                                               group_by, sort)
    for t in test_stat_list:
        print('{} - {}:'.format(t.task_name, t.test_file))
        print('\tpass: {}, fail: {}'.format(t.num_pass, t.num_fail))
        print('\taverage runtime: {}'.format(t.avg_duration_pass))


def main():
    return cli(obj={})
