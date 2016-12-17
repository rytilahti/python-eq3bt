from bluepy_devices.devices.eq3btsmart import EQ3BTSmartThermostat
import logging
import click

pass_dev = click.make_pass_decorator(EQ3BTSmartThermostat)

@click.group(invoke_without_command=True)
@click.option('--mac', envvar="EQ3_MAC")
@click.option('--debug/--normal', default=False)
@click.pass_context
def cli(ctx, mac, debug):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    thermostat = EQ3BTSmartThermostat(mac)
    thermostat.update()
    ctx.obj = thermostat

    if ctx.invoked_subcommand is None:
        ctx.invoke(state)

@cli.command()
@click.option('--target', type=float, required=False)
@pass_dev
def temp(dev, target):
    click.echo("Current target temp: %s" % dev.target_temperature)
    if target:
        click.echo("Setting target temp: %s" % target)
        dev.target_temperature = target

@cli.command()
@click.option('--target', type=int, required=False)
@pass_dev
def mode(dev, target):
    click.echo("Current mode: %s" % dev.mode_readable)
    if target:
        click.echo("Setting mode: %s" % target)
        dev.mode = target

@cli.command()
@click.option('--target', type=bool, required=False)
@pass_dev
def boost(dev, target):
    click.echo("Boost: %s" % dev.boost)
    if target is not None:
        click.echo("Setting boost: %s" % target)
        dev.boost = target

@cli.command()
@pass_dev
def valve_state(dev):
    click.echo("Valve: %s" % dev.valve_state)

@cli.command()
@click.option('--target', type=bool, required=False)
@pass_dev
def locked(dev, target):
    click.echo("Locked: %s" % dev.locked)
    if target is not None:
        click.echo("Setting lock: %s" % target)
        dev.locked = target

@cli.command()
@pass_dev
def low_battery(dev):
    click.echo("Batter low: %s" % dev.low_battery)

@cli.command()
@click.option('--temp', type=float, required=False)
@click.option('--duration', type=float, required=False)
@pass_dev
def window_open(dev, temp, duration):
    click.echo("Window open: %s" % dev.window_open)
    if temp and duration:
        click.echo("Setting window open conf, temp: %s duration: %s" % (temp, duration))
        dev.window_open_config(temp, duration)

@cli.command()
@click.option('--comfort', type=float)
@click.option('--eco', type=float)
@pass_dev
def presets(dev, comfort, eco):
    click.echo("Setting presets: comfort %s, eco %s" % (comfort, eco))
    dev.temperature_presets(comfort, eco)

@cli.command()
@click.pass_context
def state(ctx):
    dev = ctx.obj
    click.echo(dev)
    ctx.invoke(locked, ctx)
    ctx.invoke(low_battery, ctx)
    ctx.invoke(window_open, ctx)
    ctx.invoke(boost, ctx)
    ctx.invoke(temp, ctx)
    ctx.invoke(mode, ctx)
    ctx.invoke(valve_state, ctx)

if __name__ == "__main__":
    cli()