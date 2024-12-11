import {
  BotMessageSquareIcon,
  CheckSquare,
  Square,
  ExternalLink,
  FileText,
  Check,
  User,
  BarChart2,
  LineChart,
  PieChart,
  BookmarkPlus,
} from "lucide-react";
import React, { useState, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { motion, AnimatePresence } from "framer-motion";
import { Bar, Line, Pie } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import {
  Description,
  Dialog,
  DialogPanel,
  DialogTitle,
} from "@headlessui/react";
import { notesApi } from "../../utils/api";
import { useNavigate } from "react-router-dom";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

// Avatar Component
export const Avatar = ({ isUser }) => (
  <div
    className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
      isUser ? "bg-blue-500" : "bg-purple-500"
    }`}
  >
    {isUser ? (
      <User size={18} className="text-white" />
    ) : (
      <BotMessageSquareIcon size={18} className="text-white" />
    )}
  </div>
);

// Message Content Component
const MessageContent = ({
  content,
  isUser,
  processBotMessage,
  isFirstInGroup,
  isLastInGroup,
}) => {
  const { text, citations } = processBotMessage();
  const [selectedText, setSelectedText] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const navigate = useNavigate();

  const handleMouseUp = useCallback(() => {
    const selection = window.getSelection();
    if (selection && selection.toString().trim().length > 0) {
      setSelectedText(selection.toString().trim());
    }
  }, []);

  const handleAddToNotes = useCallback(() => {
    setIsDialogOpen(true);
  }, []);

  const handleSaveNote = useCallback(async () => {
    if (selectedFile) {
      try {
        await notesApi.createNote(selectedFile, selectedText);
        setIsDialogOpen(false);
        setSelectedText("");
        setSelectedFile(null);
      } catch (error) {
        console.error("Error saving note:", error);
      }
    }
  }, [selectedFile, selectedText]);

  return (
    <div className="space-y-2 p-4" onMouseUp={handleMouseUp}>
      <div className="max-w-none relative">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeRaw]}
          className="prose prose-sm"
        >
          {text}
        </ReactMarkdown>
        {selectedText && (
          <motion.button
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute top-0 right-0 p-2 bg-blue-500 text-white rounded-md flex items-center"
            onClick={handleAddToNotes}
          >
            <BookmarkPlus size={16} className="mr-1" />
            Add to Notes
          </motion.button>
        )}
      </div>
      {citations.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2">
          {citations.map((citation, index) => {
            const parts = citation.split("/");
            const id = parts[0];
            let name, pageNo;
            if (parts.length > 2) {
              name = parts.slice(1, -1).join("/");
              pageNo = parts.at(-1);
            } else {
              name = parts[1];
            }

            const onClick = () => {
              localStorage.setItem(
                "pdf_req_url",
                `http://localhost:8000/spaces/1/file/download?path=${name}`
              );
              localStorage.setItem("pdf_req_pageno", pageNo);
              navigate(`/app/storage/pdf`);
            };

            return (
              <motion.a
                key={index}
                target="_blank"
                rel="noopener noreferrer"
                className="cursor-pointer inline-flex items-center px-2 py-1 text-sm bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100 transition-colors"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={(e) => {
                  e.preventDefault();
                  onClick();
                }}
              >
                <ExternalLink size={14} className="mr-1" />
                {id}. {name} {pageNo ? `(pg. ${pageNo})` : ""}
              </motion.a>
            );
          })}
        </div>
      )}

      {/* <Dialog
        open={isDialogOpen}
        onClose={() => setIsDialogOpen(false)}
        className="fixed inset-0 z-10 overflow-y-auto"
      >
        <div className="flex items-center justify-center min-h-screen">
          <Dialog.Overlay className="fixed inset-0 bg-black opacity-30" />
          <div className="relative bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <Dialog.Title className="text-lg font-medium mb-4">
              Add to Notes
            </Dialog.Title>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Citation File
                </label>
                <div className="space-y-2">
                  {citations.map((citation, index) => {
                    const [_, id, rest] = citation.match(/^(\d+)\/(.*)/) || [];
                    if (!rest?.includes('://')) {
                      return (
                        <div
                          key={index}
                          className={`p-2 rounded-md cursor-pointer ${
                            selectedFile === rest
                              ? 'bg-blue-50 border border-blue-500'
                              : 'bg-gray-50 hover:bg-gray-100'
                          }`}
                          onClick={() => setSelectedFile(rest)}
                        >
                          <FileText size={14} className="inline mr-2" />
                          Source {id}
                        </div>
                      );
                    }
                    return null;
                  })}
                </div>
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
                  onClick={() => setIsDialogOpen(false)}
                >
                  Cancel
                </button>
                <button
                  className="px-4 py-2 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50"
                  onClick={handleSaveNote}
                  disabled={!selectedFile}
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        </div>
      </Dialog> */}
    </div>
  );
};

// Intermediate Question Component
const IntermediateQuestion = ({ question, onAnswerSubmit }) => {
  const [answer, setAnswer] = useState("");
  const [selectedOptions, setSelectedOptions] = useState([]);
  const isMultipleChoice =
    Array.isArray(question.options) && question.options.length > 0;
  const isAnswered = question.answer !== undefined;

  const handleOptionClick = (option) => {
    setSelectedOptions((prev) =>
      prev.includes(option)
        ? prev.filter((item) => item !== option)
        : [...prev, option]
    );
  };

  const handleSubmitAnswer = (e) => {
    e.preventDefault();
    if (answer.trim() || selectedOptions.length > 0) {
      onAnswerSubmit(question.id, answer.trim() || selectedOptions);
      setAnswer("");
      setSelectedOptions([]);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="mt-4 bg-white border border-gray-200 rounded-lg overflow-hidden"
    >
      <div className="flex items-start p-4">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-3">
          <BotMessageSquareIcon size={18} className="text-blue-600" />
        </div>
        <div className="flex-1">
          <h4 className="text-gray-700 mb-3">{question.question}</h4>

          {isAnswered ? (
            <div className="bg-gray-50 p-3 rounded-md border border-gray-200">
              <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                <Check size={16} className="text-green-500" />
                <span>Answered</span>
              </div>
              <div className="text-gray-700">
                {Array.isArray(question.answer)
                  ? question.answer.join(", ")
                  : question.answer}
              </div>
            </div>
          ) : isMultipleChoice ? (
            <div className="space-y-2">
              {question.options.map((option, idx) => (
                <button
                  key={idx}
                  onClick={() => handleOptionClick(option)}
                  className="flex items-center w-full p-3 text-left border rounded-md hover:bg-gray-50 transition-colors"
                >
                  {selectedOptions.includes(option) ? (
                    <CheckSquare size={18} className="text-blue-500 mr-2" />
                  ) : (
                    <Square size={18} className="text-gray-400 mr-2" />
                  )}
                  {option}
                </button>
              ))}
              {selectedOptions.length > 0 && (
                <button
                  onClick={handleSubmitAnswer}
                  className="mt-3 w-full py-2 px-4 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
                >
                  Submit Answer
                </button>
              )}
            </div>
          ) : (
            <form onSubmit={handleSubmitAnswer} className="space-y-3">
              <input
                type="text"
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                className="w-full p-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                placeholder="Type your answer..."
              />
              <button
                type="submit"
                className="w-full py-2 px-4 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
                disabled={!answer.trim()}
              >
                Submit Answer
              </button>
            </form>
          )}
        </div>
      </div>
    </motion.div>
  );
};

// Chart Component
const ChartComponent = ({ chart }) => {
  const chartIcons = {
    bar: <BarChart2 size={18} className="text-blue-600" />,
    line: <LineChart size={18} className="text-blue-600" />,
    pie: <PieChart size={18} className="text-blue-600" />,
  };

  const getChartOptions = (type) => {
    const baseOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "top",
          align: "center",
          labels: {
            padding: 8,
            usePointStyle: true,
            pointStyle: "circle",
            boxWidth: 6,
            boxHeight: 6,
            font: {
              size: 10,
              family: "'Inter', sans-serif",
            },
          },
        },
        title: {
          display: false,
        },
        tooltip: {
          backgroundColor: "rgba(255, 255, 255, 0.95)",
          titleColor: "#1f2937",
          bodyColor: "#4b5563",
          borderColor: "rgba(0, 0, 0, 0.1)",
          borderWidth: 1,
          padding: 8,
          boxPadding: 3,
          usePointStyle: true,
          bodyFont: {
            size: 10,
            family: "'Inter', sans-serif",
          },
          titleFont: {
            size: 11,
            family: "'Inter', sans-serif",
            weight: "600",
          },
        },
      },
      animation: {
        duration: 500,
        easing: "easeOutQuart",
      },
    };

    if (type === "bar" || type === "line") {
      return {
        ...baseOptions,
        scales: {
          x: {
            grid: {
              display: false,
            },
            ticks: {
              maxRotation: 45,
              minRotation: 45,
              padding: 5,
              font: {
                size: 10,
                family: "'Inter', sans-serif",
              },
            },
          },
          y: {
            beginAtZero: true,
            grid: {
              color: "rgba(0, 0, 0, 0.06)",
              drawBorder: false,
            },
            ticks: {
              padding: 5,
              font: {
                size: 10,
                family: "'Inter', sans-serif",
              },
            },
          },
        },
      };
    }

    if (type === "pie") {
      return {
        ...baseOptions,
        plugins: {
          ...baseOptions.plugins,
          legend: {
            ...baseOptions.plugins.legend,
            position: "right",
            labels: {
              ...baseOptions.plugins.legend.labels,
              padding: 10,
            },
          },
        },
      };
    }

    return baseOptions;
  };

  const getDatasetStyle = (index, type) => {
    const colors = [
      "rgba(66, 133, 244, 0.8)", // Google Blue
      "rgba(234, 67, 53, 0.8)", // Google Red
      "rgba(251, 188, 4, 0.8)", // Google Yellow
      "rgba(52, 168, 83, 0.8)", // Google Green
      "rgba(103, 58, 183, 0.8)", // Purple
      "rgba(255, 152, 0, 0.8)", // Orange
    ];

    const baseStyle = {
      backgroundColor: colors[index % colors.length],
      borderColor: colors[index % colors.length].replace("0.8", "1"),
      borderWidth: 1.5,
      hoverBackgroundColor: colors[index % colors.length].replace("0.8", "0.9"),
      hoverBorderColor: colors[index % colors.length].replace("0.8", "1"),
      hoverBorderWidth: 2,
    };

    if (type === "line") {
      return {
        ...baseStyle,
        fill: false,
        tension: 0.3,
        pointRadius: 3,
        pointHoverRadius: 5,
        pointBackgroundColor: colors[index % colors.length].replace("0.8", "1"),
        pointBorderColor: "#fff",
        pointBorderWidth: 1.5,
        pointHoverBackgroundColor: "#fff",
        pointHoverBorderColor: colors[index % colors.length].replace(
          "0.8",
          "1"
        ),
      };
    }

    if (type === "pie") {
      return {
        backgroundColor: colors.map((color) => color.replace("0.8", "0.75")),
        borderColor: colors.map((color) => color.replace("0.8", "1")),
        borderWidth: 1,
        hoverBackgroundColor: colors.map((color) =>
          color.replace("0.8", "0.85")
        ),
        hoverBorderColor: colors.map((color) => color.replace("0.8", "1")),
        hoverBorderWidth: 2,
        hoverOffset: 4,
      };
    }

    return baseStyle;
  };

  const getChartComponent = () => {
    const chartData = {
      ...chart.data,
      datasets: chart.data.datasets.map((dataset, index) => ({
        ...dataset,
        ...getDatasetStyle(index, chart.chart_type),
      })),
    };

    const commonProps = {
      options: getChartOptions(chart.chart_type),
      data: chartData,
    };

    switch (chart.chart_type) {
      case "bar":
        return <Bar {...commonProps} />;
      case "line":
        return <Line {...commonProps} />;
      case "pie":
        return <Pie {...commonProps} />;
      default:
        return null;
    }
  };

  return (
    <div className="w-full max-w-lg bg-white rounded-lg shadow-sm overflow-hidden">
      <div className="p-2 border-b flex items-center gap-2">
        {chartIcons[chart.chart_type]}
        <span className="font-medium text-gray-700 text-xs">
          {chart.title ||
            `${
              chart.chart_type.charAt(0).toUpperCase() +
              chart.chart_type.slice(1)
            } Chart`}
        </span>
      </div>
      <div className="p-2">
        <div className="aspect-[16/9] w-full" style={{ height: "200px" }}>
          {getChartComponent()}
        </div>
      </div>
    </div>
  );
};

const KpiAnalysisDialog = ({ kpiAnalysis }) => {
  const [isKpiDialogOpen, setIsKpiDialogOpen] = useState(false);
  return (
    <>
      <button
        onClick={() => setIsKpiDialogOpen(true)}
        className="rounded-md w-full bg-bluecolor/20 py-2 px-4 text-sm font-medium focus:outline-none data-[hover]:bg-black/30 data-[focus]:outline-1 data-[focus]:outline-white ml-auto"
      >
        View Financial Analysis (using KPIs)
      </button>
      <Dialog
        open={isKpiDialogOpen}
        as="div"
        className="relative z-10 focus:outline-none"
        onClose={() => setIsKpiDialogOpen(false)}
      >
        <div className="fixed inset-0 bg-black/75 z-10 w-screen overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <DialogPanel
              transition
              className="max-w-[45rem] rounded-xl bg-white p-6 backdrop-blur-2xl duration-300 ease-out data-[closed]:transform-[scale(95%)] data-[closed]:opacity-0"
            >
              <DialogTitle as="h3" className="text-3xl font-medium">
                Key Performance Indicators Analysis
              </DialogTitle>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                className="prose prose-sm"
              >
                {kpiAnalysis}
              </ReactMarkdown>
              <div className="mt-4">
                <button
                  className="inline-flex items-center gap-2 rounded-md bg-bluecolor py-1.5 px-3 text-sm/6 font-semibold text-white shadow-inner shadow-white/10 focus:outline-none data-[hover]:bg-gray-600 data-[focus]:outline-1 data-[focus]:outline-white data-[open]:bg-gray-700"
                  onClick={() => setIsKpiDialogOpen(false)}
                >
                  Got it, thanks!
                </button>
              </div>
            </DialogPanel>
          </div>
        </div>
      </Dialog>
    </>
  );
};

// Main ChatMessage Component
const ChatMessage = ({
  content,
  isUser,
  intermediate_questions = [],
  charts = [],
  kpiAnalysis = null,
  onAnswerSubmit,
  isFirstInGroup,
  isLastInGroup,
}) => {
  const processBotMessage = () => {
    if (!content) return { text: "", citations: [] };

    const citations = [];
    const segments = content.split(/(\[\[.+?\]\])/g);
    const text = segments
      .map((segment) => {
        if (segment.startsWith("[[") && segment.endsWith("]]")) {
          const citation = segment.slice(2, -2);
          citations.push(citation);
          return `<sup><u>${citation.split("/")[0]}</u></sup>`;
        }
        return segment;
      })
      .join("");

    return { text, citations };
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex flex-col ${
        isUser ? "text-gray-800" : "text-gray-800"
      } w-full`}
    >
      <MessageContent
        content={content}
        isUser={isUser}
        processBotMessage={processBotMessage}
        isFirstInGroup={isFirstInGroup}
        isLastInGroup={isLastInGroup}
      />

      {charts && charts.length > 0 && (
        <div className="px-4 pb-4 space-y-3 flex gap-4 items-center">
          {charts.map((chart, index) => (
            <ChartComponent key={index} chart={chart} />
          ))}
        </div>
      )}

      {kpiAnalysis && (
        <div className="pb-4 w-full px-6">
          <KpiAnalysisDialog kpiAnalysis={kpiAnalysis} />
        </div>
      )}

      {!content &&
        intermediate_questions &&
        intermediate_questions.length > 0 && (
          <div className="px-4 pb-4">
            {intermediate_questions.map((question, index) => (
              <IntermediateQuestion
                key={index}
                question={question}
                onAnswerSubmit={onAnswerSubmit}
              />
            ))}
          </div>
        )}
    </motion.div>
  );
};

export default ChatMessage;
