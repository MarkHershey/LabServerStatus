# LabServerStatus

## Install Client on Lab Workstation

Step 0: Navigate to project root

```bash
git clone https://github.com/MarkHershey/LabServerStatus.git
cd LabServerStatus
```

Step 1: Create a runner script

-   Give current machine a unique name
    -   Modify [create-runner-script](create-runner-script) at [Line 53](https://github.com/MarkHershey/LabServerStatus/blob/285e56231934276a91110d59ccf00513d7ed5f08/create-runner-script#L53) and save the changes.
-   Run the script

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
