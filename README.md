# LabServerStatus

## Install Client on Lab Workstation

Step 0: Navigate to project root

```bash
cd LabServerStatus
```

Step 1: Create a runner script

```bash
./create-runner-script
```

Step 2: Setup a Cron job to run the runner script on system startup

-   Edit Cron job file

    ```bash
    sudo crontab -e
    ```

-   Add this line to the end of the file

    ```
    @reboot /bin/run_system_status_client &
    ```

Step 3: Reboot the system

```bash
sudo reboot
```
