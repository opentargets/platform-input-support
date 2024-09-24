# Open Targets: platform-input-support

Fetch, validate and arrange the data required by the Open Targets Platform ETL pipeline.


## Installation and running
PIS uses [UV](https://docs.astral.sh/uv/) as its package manager. It is compatible with PIP,
so you can also fall back to it if you feel more comfortable.

> [!NOTE]
> PIS will be uploaded to [Pypi](https://pypi.org/project/platform-input-support/) once it is ready to
> use. In the meantime, you can run it locally with make or directly by using uv:

To run PIS with UV, you can use the following commands:

```bash
uv run pis -h
```

it handles the installation of the dependencies in a virtual environment and runs the application, so
it would be similar to:

```bash
virtualenv .venv
source .venv/bin/activate
pip install .
pis -h
```

> [!TIP]
> You can also use PIS with [GNU Make](https://www.gnu.org/software/make/). Running `make` without
any target shows help.


### Running with Docker
PIS can be run in Docker. To run with Docker, you must have a credentials file for GCP so there is a
way to authenticate inside the container environment. Assuming you do, you can run the following
command:

```bash
docker run \
  -v /path/to/credentials.json:/app/credentials.json \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \
  quay.io/opentargets/platform-input-support-test:latest -h
```

To build your own Docker image, run the following command from the root of the repository:

```bash
docker build -t pis .
```

## Development

> [!NOTE]
> Take a look at the [API documentation](https://javfg.github.io/platform-input-support),
> it is a very helpful guide when developing new tasks.

> [!IMPORTANT]
> Remember to run `make dev` before starting development. This will set up a very simple git hook
> that does a few checks before committing.

Development of PIS can be done straight away in the local environment. You can run the application
just like before (`uv run pis`) to check the changes you make. Alternatively, you can run the app
from inside the virtual environment:

```bash
source .venv/bin/activate
pis -h
```

You can test the changes by running a small step, like `so`:

```bash
uv run pis --step so
```

---

# Structure
PIS is designed to run a series of steps which prepare the data for the Open Targets Platform ETL.
Only one step is run in every execution, but the idea is still to run them all, we'll call this a
pipeline run (although the Platform pipeline is larger, PIS is just the first part).

If needed, a simple bash `for` loop could be used to run multiple steps:

```bash
for step in go so; do (pis -s $step) &; done; wait
```

But the idea is to put PIS into [the orchestrator](https://github.com/opentargets/orchestration), which
uses [Apache Airflow](https://airflow.apache.org/) to run the steps in parallel.

The different steps are defined as a series of tasks in the configuration file. Those tasks must always
generate a resource. That resource will be used by the next step in the pipeline. The resource is
validated and uploaded to a Google Cloud Storage bucket.

## Flow summary
One execution of PIS will perform the following:

1. Parse command line options, environment variables and configuration file.
2. Initialize the application by setting up logging and the Google Cloud Storage client.
3. Load the available tasks into a registry.
4. Ensure the local work directory exists and is writable.
5. Run the step, which is divided into four phases:
   1. **Initialization**: A series of _pretasks_ that prepare the execution of the step. Examples are
       getting a file list, or dynamically spawning tasks to run in the main phase.
   2. **Staging**: Main phase of the step. It is made of _tasks_ that perform the actual work. Examples of
       tasks are downloading a file from a remote location, or fetching an index from elasticsearch.
   3. **Validation**: Once tasks have run, a series of validators is executed on the results.
   4. **Upload**: The resulting resources are uploaded to a Google Cloud Storage bucket.
6. Write a report of the execution to a manifest file.

> [!IMPORTANT]
In the staging, validation and upload phases, the tasks are run in parallel.

## Pretasks and Tasks
Pretasks and tasks are defined in the `tasks` module. They both inherit from a base class that provides
some common functionality and defines the interface that a task must implement.

A task is a class that defines a `run` method. This method is called by the pipeline runner and is
where the actual work is done. The task can also define a `validate` and an `upload` method. Those
are optional. Not implementing a `validate` means no validation will be run on the results of the task.
`upload` is not usually needed as the base class provides a default implementation.

> [!WARNING]
> The `run`, `validate` and `upload` methods must return `self`. This is because the pipeline runner
> uses the return value to know the state of the task.

> [!TIP]
> The `run`, `validate` and `upload` methods have an `abort` [Event](https://docs.python.org/3/library/threading.html#threading.Event) argument that can be used to stop the execution of the task when a general abort
> signal is produced anywhere in the step run. This is useful, for example, to stop a download early
> when another task fails.

### Task definition
Tasks will be spawned from a registry by parsing the configuration file and using the first word in the
task name as the task class name. So for example, if a task is defined as:

```yaml
- name: download an example file
  source: https://example.com/file.txt
  destination: /path/to/file.txt
```

PIS will spawn a `Download` task with the arguments `source` and `destination`.

Each task can have a different set of arguments, which are defined in `TaskDefinition` class. There are
two requirements for the arguments of a task:

* __All__ tasks, including pretasks, must have a `name` argument, for obvious reasons.
* __Main__ tasks must have a `destination` argument. This is to remember implementers that the purpose
  of a task is to generate something that will be used by the next step in the pipeline.

There is an example task: [`HelloWorld`](platform_input_support/tasks/hello_world.py).

## Validators
Validators are defined in the `validators` module. They are just functions that return a boolean value.
They will be run in the `validate` method of tasks, by using the `v` wrapper. `v` takes a validator and
a list of arguments to pass to it. If during the execution of the `validate` method, any call to `v`
returns `False`, the validation will stop, raise a `ValidationError` and the task will be marked as
failed.

## Manifest
PIS automatically generates a report of every execution. This report is appended into a JSON file that
is overarching to a complete run of the pipeline (all the steps).

The manifest file contains:
- A log of the executions in the context of a whole pipeline run, including a timestamp, duration and
  a summary of the state the whole  is in after that.
- A report for the last run of each step in the pipeline. The report includes the state of the step,
  the duration of the execution, a very simple log of what happened and a list of the resources
  generated by the step.
- For each step, a list of reports on all the tasks run by it. These include the resulting state of
  the task, the timestamp, a detailed log, and the whole configuration of the task.

Once a step run has finished, PIS attempts to retrieve a previous manifest from the Google Cloud Storage
bucket or the local work directory. If it finds one, it will append the new report to it. Then, the
new manifest is uploaded again, as well as written locally.

The manifest management is automated in the tasks, so there is no need to handle it. The base class
will take care of it. Any errors raised will be caught and logged, and any logs will be also directed
to a handler that writes to the manifest.
