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
@click.option('-t', '--tasks', multiple=True)
def test_stats(ctx, after_date, before_date, tasks):
    api = ctx.obj['api']
    params = {
        'after_date': after_date,
        'before_date': before_date,
    }
    if tasks:
        params['tasks'] = tasks

    test_stat_list = api.test_stats_by_project(project_id, params)
    for t in test_stat_list:
        print(t.test_file)


def main():
    return cli(obj={})


if __name__ == '__main__':
    main()
