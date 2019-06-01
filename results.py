import ui

MAX_WIND_TEMPLATE = 'MAX FROM {direction:03.0f}° -> {strength:.{precision}f}{units}'
NO_MAX_WIND_TEMPLATE = 'MAX FROM {direction:03.0f}° -> NO MAX'
PRECISION = 1


class GridResultsTableSource(ui.ListDataSource):
    """
    DataSource and delegate for the grid results tableview
    """
    def load_from_results_dict(self, results_dict):
        self.items = [(direction, speed)
                      for direction, speed in results_dict.items()]
        self.reload()

    def tableview_cell_for_row(self, tableview, section, row):
        cell = ui.TableViewCell()
        data = self.items[row]
        cell.text_label.text = self.format_results_text_line(
            data[0], data[1], PRECISION)
        return cell

    @staticmethod
    def format_results_text_line(direction, speed, precision=1):
        """
        Return a formatted grid results line from a direction, speed, and precision.
        If an exception occurs, return the error string.
        """
        precision = precision if precision >= 0 else 5
        try:
            if speed != -1:
                return MAX_WIND_TEMPLATE.format(
                    direction=direction,
                    strength=speed,
                    precision=precision,
                    units='kts')
            else:
                return NO_MAX_WIND_TEMPLATE.format(direction=direction)
        except Exception as e:
            return str(e)

def make_grid_view(results):
    """
    Return a TableView populate with the results of a grid 
    calculation.
    """
    grid_table = ui.load_view('results')['grid_table']
    grid_table.data_source = GridResultsTableSource([])
    grid_table.delegate = grid_table.data_source
    grid_table.data_source.load_from_results_dict(results)
    return grid_table

