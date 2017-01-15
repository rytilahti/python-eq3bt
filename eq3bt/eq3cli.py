""" Cli tool for testing connectivity with EQ3 smart thermostats. """
import logging
import click

from eq3bt import Thermostat

pass_dev = click.make_pass_decorator(Thermostat)


@click.group(invoke_without_command=True)
@click.option('--mac', envvar="EQ3_MAC")
@click.option('--debug/--normal', default=False)
@click.pass_context
def cli(ctx, mac, debug):
    """ Tool to query and modify the state of EQ3 BT smart thermostat. """
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    thermostat = Thermostat(mac)
    thermostat.update()
    ctx.obj = thermostat

    if ctx.invoked_subcommand is None:
        ctx.invoke(state)


@cli.command()
@click.option('--target', type=float, required=False)
@pass_dev
def temp(dev, target):
    """ Gets or sets the target temperature."""
    click.echo("Current target temp: %s" % dev.target_temperature)
    if target:
        click.echo("Setting target temp: %s" % target)
        dev.target_temperature = target


@cli.command()
@click.option('--target', type=int, required=False)
@pass_dev
def mode(dev, target):
    """ Gets or sets the active mode. """
    click.echo("Current mode: %s" % dev.mode_readable)
    if target:
        click.echo("Setting mode: %s" % target)
        dev.mode = target


@cli.command()
@click.option('--target', type=bool, required=False)
@pass_dev
def boost(dev, target):
    """ Gets or sets the boost mode. """
    click.echo("Boost: %s" % dev.boost)
    if target is not None:
        click.echo("Setting boost: %s" % target)
        dev.boost = target


@cli.command()
@pass_dev
def valve_state(dev):
    """ Gets the state of the valve. """
    click.echo("Valve: %s" % dev.valve_state)


@cli.command()
@click.option('--target', type=bool, required=False)
@pass_dev
def locked(dev, target):
    """ Gets or sets the lock. """
    click.echo("Locked: %s" % dev.locked)
    if target is not None:
        click.echo("Setting lock: %s" % target)
        dev.locked = target


@cli.command()
@pass_dev
def low_battery(dev):
    """ Gets the low battery status. """
    click.echo("Batter low: %s" % dev.low_battery)


@cli.command()
@click.option('--temp', type=float, required=False)
@click.option('--duration', type=float, required=False)
@pass_dev
def window_open(dev, temp, duration):
    """ Gets and sets the window open settings. """
    click.echo("Window open: %s" % dev.window_open)
    if temp and duration:
        click.echo("Setting window open conf, temp: %s duration: %s" % (temp, duration))
        dev.window_open_config(temp, duration)


@cli.command()
@click.option('--comfort', type=float)
@click.option('--eco', type=float)
@pass_dev
def presets(dev, comfort, eco):
    """ Sets the preset temperatures for auto mode. """
    click.echo("Setting presets: comfort %s, eco %s" % (comfort, eco))
    dev.temperature_presets(comfort, eco)

@cli.command()
@pass_dev
def schedule(dev):
    """ Gets the schedule from the thermostat. """
    # TODO: expose setting the schedule somehow?
    for d in range(7):
        dev.query_schedule(d)
    for day in dev.schedule.values():
        click.echo("Day %s, base temp: %s" % (day.day, day.base_temp))
        current_hour = day.next_change_at
        for hour in day.hours:
            if current_hour == 0: continue
            click.echo("\t[%s-%s] %s" % (current_hour, hour.next_change_at, hour.target_temp))
            current_hour = hour.next_change_at

@cli.command()
@click.argument('offset', type=float)
@pass_dev
def offset(dev, offset):
    """ Sets the temperature offset [-3,5 3,5] """
    click.echo("Setting the offset to %s" % offset)
    dev.temperature_offset(offset)

@cli.command()
@click.pass_context
def state(ctx):
    """ Prints out all available information. """
    dev = ctx.obj
    click.echo(dev)
    ctx.invoke(locked, ctx)
    ctx.invoke(low_battery, ctx)
    ctx.invoke(window_open, ctx)
    ctx.invoke(boost, ctx)
    ctx.invoke(temp, ctx)
    # ctx.invoke(presets, ctx)
    ctx.invoke(mode, ctx)
    ctx.invoke(valve_state, ctx)


if __name__ == "__main__":
    cli()
